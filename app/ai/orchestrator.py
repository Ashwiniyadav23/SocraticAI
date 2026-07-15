"""
Orchestrator — Section 11.5. A deterministic service (not an LLM call) that
owns the state machine + mode selector and sequences the agent calls per the
diagram in Section 11.6:

  Diagnostic Agent (seq)
    -> [Misconception Agent, Confidence/Overload heuristic] (parallel)
    -> Orchestrator: state machine + mode selector
    -> Socratic Questioning Agent (seq)
    -> Answer-Leak Guard (seq, final gate)
    -> (if state in APPLYING/REFLECTING) Mastery Assessment Agent
"""
import asyncio
import hashlib
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import diagnostic_agent, misconception_agent, socratic_agent, mastery_agent
from app.ai import behavior_engine as heuristics
from app.agents.answer_leak_guard import check_leak
from app.config import settings
from app.hint_ladder import next_tier, tier_instruction
from app.mode_selector import select_mode
from app.models import Concept, HintLog, LearningSession, SessionTurn
from app.ai.memory.manager import append_message, get_working_memory
from app.ai.state_manager import LearnerState, Signals, transition

logger = logging.getLogger("orchestrator")

FALLBACK_HINT_TEMPLATE = (
    "Let's slow down for a second. Looking at what you've got so far — "
    "what's the very first thing you're unsure about? Start there."
)

FALLBACK_LLM_UNAVAILABLE = (
    "I'm having a little trouble thinking right now (LLM service unavailable). "
    "Let's keep going — can you tell me what you've tried so far?"
)


from fastapi import BackgroundTasks
from app.ai.events import trigger_dna_update

async def run_turn(
    db: AsyncSession,
    session: LearningSession,
    concept: Concept,
    student_message: str,
    user_selected_mode: str | None = None,
    background_tasks: BackgroundTasks | None = None,
) -> dict:
    session_id = str(session.id)

    # ---- 0. working memory ----
    mem = await get_working_memory(session_id)
    recent_turns = mem["messages"]
    await append_message(session_id, "student", student_message)

    learning_context = None
    if session.context_id:
        from app.models import SessionContext
        ctx = await db.get(SessionContext, session.context_id)
        if ctx:
            learning_context = {
                "purpose": ctx.purpose,
                "urgency": ctx.urgency,
                "deadline": ctx.deadline.isoformat() if ctx.deadline else None,
                "expected_depth": ctx.expected_depth,
                "objective": ctx.objective
            }

    state_input = {
        "concept_name": concept.name,
        "concept_domain": concept.domain,
        "canonical_facts": concept.canonical_facts,
        "recent_turns": recent_turns,
        "student_message": student_message,
        "session_unresolved_turns": session.unresolved_turns,
        "session_hint_tier": session.hint_tier,
        "session_current_state": session.current_state,
        "user_selected_mode": user_selected_mode,
        "learning_context": learning_context,
        "diag": None,
        "misconception_result": None,
        "signals": None,
        "new_state": None,
        "mode": None,
        "new_tier": None,
        "unresolved": None,
        "tutor_message": None,
        "leak_triggered": None,
        "session_id": session_id,
        "target_node": None,
        "constraints": None
    }
    
    from app.ai.graphs.tutor_graph import tutor_graph
    
    result_state = await tutor_graph.ainvoke(state_input)
    
    new_state_value = result_state["new_state"]
    mode = result_state["mode"]
    new_tier = result_state["new_tier"]
    unresolved = result_state["unresolved"]
    tutor_message = result_state["tutor_message"]
    leak_triggered = result_state["leak_triggered"] or False

    db.add(HintLog(
        session_id=session.id,
        tier=new_tier,
        content_hash=hashlib.sha256(tutor_message.encode()).hexdigest()[:16],
        was_leak_flagged=leak_triggered,
    ))

    # ---- 6. Persist turns ----
    db.add(SessionTurn(session_id=session.id, role="student", content=student_message,
                        mode=mode, hint_tier=new_tier, learner_state=new_state_value))
    db.add(SessionTurn(session_id=session.id, role="tutor", content=tutor_message,
                        mode=mode, hint_tier=new_tier, learner_state=new_state_value))

    session.current_state = new_state_value
    session.current_mode = mode
    session.hint_tier = new_tier
    session.unresolved_turns = unresolved
    db.add(session)
    await db.commit()

    await append_message(session_id, "tutor", tutor_message)

    signals = result_state.get("signals")
    if background_tasks and signals:
        signals_dict = {
            "ai_dependency_signals": signals.shared_ai_usage,
            "curiosity_score": signals.curiosity_score,
            "stuck": signals.stuck
        }
        background_tasks.add_task(trigger_dna_update, session.user_id, signals_dict)

    return {
        "tutor_message": tutor_message,
        "learner_state": new_state_value,
        "mode": mode,
        "hint_tier": new_tier,
        "leak_guard_triggered": leak_triggered,
    }


async def run_mastery_check(concept_name: str, evidence: dict) -> dict:
    """Invoked only on state transitions into APPLYING/REFLECTING (cost control,
    Section 11.5) — call explicitly from the reflection/assessment routers."""
    from app.ai.graphs.reflection_graph import reflection_graph
    
    state_input = {
        "concept_name": concept_name,
        "evidence": evidence,
        "mastery_result": None
    }
    
    result = await reflection_graph.ainvoke(state_input)
    return result["mastery_result"]
