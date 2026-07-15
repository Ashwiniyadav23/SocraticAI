import operator
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END

from app.agents import diagnostic_agent, misconception_agent, socratic_agent
from app.ai import behavior_engine as heuristics
from app.agents.answer_leak_guard import check_leak
from app.hint_ladder import next_tier, tier_instruction
from app.mode_selector import select_mode
from app.ai.state_manager import LearnerState, Signals, transition
from app.config import settings

class TutorState(TypedDict):
    concept_name: str
    concept_domain: str
    canonical_facts: dict
    recent_turns: list
    student_message: str
    session_unresolved_turns: int
    session_hint_tier: int
    session_current_state: str
    user_selected_mode: str | None
    
    # populated by nodes
    diag: dict | None
    misconception_result: dict | None
    signals: Signals | None
    new_state: str | None
    mode: str | None
    new_tier: int | None
    unresolved: int | None
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


async def orchestrator_node(state: TutorState) -> dict:
    student_message = state["student_message"]
    diag = state["diag"] or {}
    misc = state["misconception_result"] or {}
    
    prior_lens = [len(t["content"].split()) for t in state["recent_turns"] if t["role"] == "student"]
    prior_avg = sum(prior_lens) / len(prior_lens) if prior_lens else 0
    hedge_freq = heuristics.hedge_word_frequency(student_message)
    stuck = heuristics.is_stuck_signal(student_message)
    overload = heuristics.overload_flag(student_message, prior_avg, state["session_unresolved_turns"])
    curiosity = heuristics.curiosity_score(student_message)
    confidence = heuristics.aggregate_confidence(
        self_rated=diag.get("confidence", 0.5),
        hedge_freq=hedge_freq,
        recent_correct_ratio=1.0 if diag.get("correct_baseline") else 0.5,
    )

    signals = Signals(
        confidence=confidence,
        misconception_flag=bool(misc.get("misconception")),
        overload_flag=overload,
        reasoning_steps=2 if len(student_message.split()) > 25 and not stuck else 0,
        stuck=stuck,
        contradiction=bool(misc.get("misconception")),
        curiosity_score=curiosity,
        transfer_solved=False,
        coherent_teach_back=False,
        correct_baseline=bool(diag.get("correct_baseline")),
        shared_ai_usage=bool(diag.get("shared_ai_usage")),
    )

    prev_state = LearnerState(state["session_current_state"])
    new_state_enum, unresolved = transition(prev_state, state["session_unresolved_turns"], signals)
    mode = select_mode(new_state_enum, signals, state["user_selected_mode"], domain=state["concept_domain"])

    new_tier = next_tier(state["session_hint_tier"], signals.stuck)

    return {
        "signals": signals,
        "new_state": new_state_enum.value,
        "mode": mode,
        "new_tier": new_tier,
        "unresolved": unresolved
    }


async def socratic_node(state: TutorState) -> dict:
    import asyncio
    hint_instr = tier_instruction(state["new_tier"])
    try:
        tutor_message = await asyncio.wait_for(
            socratic_agent.generate_response(state["mode"], state["concept_name"], state["recent_turns"], state["student_message"], hint_instr),
            timeout=settings.AGENT_TIMEOUT_SECONDS,
        )
    except Exception:
        tutor_message = "I'm having a little trouble thinking right now. Let's keep going — can you tell me what you've tried so far?"
    return {"tutor_message": tutor_message}


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
                state["mode"], state["concept_name"], state["recent_turns"], state["student_message"], hint_instr, corrective=corrective
            ),
            timeout=settings.AGENT_TIMEOUT_SECONDS,
        )
        leaked_again, _ = await check_leak(tutor_message)
        if leaked_again:
            tutor_message = "Let's slow down for a second. Looking at what you've got so far — what's the very first thing you're unsure about? Start there."
    except Exception:
        tutor_message = "Let's slow down for a second. Looking at what you've got so far — what's the very first thing you're unsure about? Start there."
        
    return {"tutor_message": tutor_message, "leak_triggered": True}


# Build Graph
builder = StateGraph(TutorState)

builder.add_node("analyze_input", analyze_input_node)
builder.add_node("orchestrator", orchestrator_node)
builder.add_node("socratic", socratic_node)
builder.add_node("leak_guard", leak_guard_node)

builder.add_edge(START, "analyze_input")
builder.add_edge("analyze_input", "orchestrator")
builder.add_edge("orchestrator", "socratic")
builder.add_edge("socratic", "leak_guard")
builder.add_edge("leak_guard", END)

tutor_graph = builder.compile()
