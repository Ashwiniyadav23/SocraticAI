import operator
from typing import Annotated, TypedDict, Any

from langgraph.graph import StateGraph, START, END

from app.agents import diagnostic_agent, misconception_agent, socratic_agent
from app.agents.answer_leak_guard import check_leak
from app.hint_ladder import next_tier, tier_instruction
from app.ai.state_manager import Signals
from app.config import settings

# ADES Imports
from app.ai.decision_engine.router import route_turn
from app.ai.context import detect_context, LearningContext

class TutorState(TypedDict):
    session_id: str | None
    concept_name: str
    concept_domain: str
    canonical_facts: dict
    recent_turns: list
    student_message: str
    session_unresolved_turns: int
    session_hint_tier: int
    session_current_state: str
    user_selected_mode: str | None
    learning_context: LearningContext | dict | None
    retrieved_context: list | None
    
    # populated by nodes
    diag: dict | None
    misconception_result: dict | None
    signals: Signals | None
    new_state: str | None
    mode: str | None
    new_tier: int | None
    unresolved: int | None
    target_node: str | None
    constraints: dict | None
    tutor_message: str | None
    leak_triggered: bool | None


async def analyze_input_node(state: TutorState) -> dict:
    import asyncio
    
    async def _diag():
        try:
            return await asyncio.wait_for(
                diagnostic_agent.run_diagnostic(state["concept_name"], state["recent_turns"], state["student_message"]),
                timeout=settings.AGENT_TIMEOUT_SECONDS,
            )
        except Exception:
            return {"confidence": 0.5, "correct_baseline": False}
            
    async def _misc():
        try:
            return await asyncio.wait_for(
                misconception_agent.run_misconception_check(state["concept_name"], state["canonical_facts"], state["student_message"]),
                timeout=settings.AGENT_TIMEOUT_SECONDS,
            )
        except Exception:
            return {"misconception": False, "confidence": 0.0}

    diag, misc = await asyncio.gather(_diag(), _misc())
    return {"diag": diag, "misconception_result": misc}


async def detect_context_node(state: TutorState) -> dict:
    # Only run LLM detection if context isn't already provided by the DB/API
    if state.get("learning_context"):
        return {}
        
    context_obj = await detect_context(state["student_message"], state["recent_turns"])
    # Convert Pydantic object to dict for graph state
    return {"learning_context": context_obj.model_dump() if hasattr(context_obj, "model_dump") else context_obj.dict()}


async def decision_engine_node(state: TutorState) -> dict:
    """The ADES Router Node."""
    return await route_turn(state, state.get("session_id"))


async def bars_node(state: TutorState) -> dict:
    from app.ai.rag.prompts import rewrite_query
    from app.ai.rag.retriever import retrieve_chunks
    from app.ai.rag.ranker import rank_chunks
    from app.database import db
    from app.models import LearningSession, SemanticMemory
    
    session_id = state.get("session_id")
    if not session_id:
        return {"retrieved_context": []}
        
    async with db.session_maker() as session_db:
        session = await session_db.get(LearningSession, session_id)
        if not session:
            return {"retrieved_context": []}
            
        semantic_memory = await session_db.get(SemanticMemory, session.user_id)
        dna = None
        weak_topics = []
        if semantic_memory:
            dna = semantic_memory.learning_style
            weak_topics = semantic_memory.weak_topics
            
        rewritten_query = await rewrite_query(state["student_message"], weak_topics, state["recent_turns"])
        chunks = await retrieve_chunks(session_db, rewritten_query, topic=state.get("concept_name"))
        ranked_chunks = rank_chunks(chunks, dna, state.get("learning_context", {}))
        
        return {"retrieved_context": [{"text": c.text, "format": c.format} for c in ranked_chunks]}


async def socratic_node(state: TutorState) -> dict:
    import asyncio
    hint_instr = tier_instruction(state["new_tier"])
    try:
        tutor_message = await asyncio.wait_for(
            socratic_agent.generate_response(state["mode"], state["concept_name"], state["recent_turns"], state["student_message"], hint_instr, retrieved_context=state.get("retrieved_context")),
            timeout=settings.AGENT_TIMEOUT_SECONDS,
        )
    except Exception:
        tutor_message = "I'm having a little trouble thinking right now. Let's keep going — can you tell me what you've tried so far?"
    return {"tutor_message": tutor_message}


async def mentor_node(state: TutorState) -> dict:
    """Placeholder for Milestone 6: Mentor Engine"""
    # For now, just return a fallback message for testing the ADES routing
    return {"tutor_message": "MENTOR INTERVENTION: It looks like you're feeling overloaded. Let's take a deep breath."}


async def reflection_node(state: TutorState) -> dict:
    """Placeholder for Milestone 8: Reflection Engine"""
    return {"tutor_message": "REFLECTION TIME: Can you summarize what we just learned?"}


async def leak_guard_node(state: TutorState) -> dict:
    import asyncio
    try:
        leaked, reason = await check_leak(state["tutor_message"])
    except Exception:
        leaked, reason = False, ""
        
    if not leaked:
        return {"leak_triggered": False}
        
    # Retry once if leaked
    corrective = "You just gave away the answer. Rephrase your last message as a guiding question instead."
    hint_instr = tier_instruction(state["new_tier"])
    try:
        tutor_message = await asyncio.wait_for(
            socratic_agent.generate_response(
                state["mode"], state["concept_name"], state["recent_turns"], state["student_message"], hint_instr, retrieved_context=state.get("retrieved_context"), corrective=corrective
            ),
            timeout=settings.AGENT_TIMEOUT_SECONDS,
        )
        leaked_again, _ = await check_leak(tutor_message)
        if leaked_again:
            tutor_message = "Let's slow down for a second. Looking at what you've got so far — what's the very first thing you're unsure about? Start there."
    except Exception:
        tutor_message = "Let's slow down for a second. Looking at what you've got so far — what's the very first thing you're unsure about? Start there."
        
    return {"tutor_message": tutor_message, "leak_triggered": True}


def route_decision(state: TutorState) -> str:
    """Conditional Edge routing function based on ADES target_node."""
    target = state.get("target_node")
    if target == "mentor_intervention":
        return "mentor_intervention"
    elif target == "reflection":
        return "reflection"
    return "socratic"


# Build Graph
builder = StateGraph(TutorState)

builder.add_node("analyze_input", analyze_input_node)
builder.add_node("detect_context", detect_context_node)
builder.add_node("decision_engine", decision_engine_node)
builder.add_node("bars_node", bars_node)
builder.add_node("socratic", socratic_node)
builder.add_node("mentor_intervention", mentor_node)
builder.add_node("reflection", reflection_node)
builder.add_node("leak_guard", leak_guard_node)

builder.add_edge(START, "analyze_input")
builder.add_edge("analyze_input", "detect_context")
builder.add_edge("detect_context", "decision_engine")
builder.add_edge("decision_engine", "bars_node")

builder.add_conditional_edges(
    "bars_node",
    route_decision,
    {
        "socratic": "socratic",
        "mentor_intervention": "mentor_intervention",
        "reflection": "reflection"
    }
)

builder.add_edge("socratic", "leak_guard")
builder.add_edge("mentor_intervention", "leak_guard")
builder.add_edge("reflection", "leak_guard")
builder.add_edge("leak_guard", END)

tutor_graph = builder.compile()
