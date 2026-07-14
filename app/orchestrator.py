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

from app.agents import diagnostic_agent, misconception_agent, socratic_agent, mastery_agent, heuristics
from app.agents.answer_leak_guard import check_leak
from app.config import settings
from app.hint_ladder import next_tier, tier_instruction
from app.mode_selector import select_mode
from app.models import Concept, HintLog, LearningSession, SessionTurn
from app.redis_client import append_message, get_working_memory
from app.state_machine import LearnerState, Signals, transition

logger = logging.getLogger("orchestrator")

FALLBACK_HINT_TEMPLATE = (
    "Let's slow down for a second. Looking at what you've got so far — "
    "what's the very first thing you're unsure about? Start there."
)

FALLBACK_LLM_UNAVAILABLE = (
    "I'm having a little trouble thinking right now (LLM service unavailable). "
    "Let's keep going — can you tell me what you've tried so far?"
)


async def run_turn(
    db: AsyncSession,
    session: LearningSession,
    concept: Concept,
    student_message: str,
    user_selected_mode: str | None = None,
) -> dict:
    session_id = str(session.id)

    # ---- 0. working memory ----
    mem = await get_working_memory(session_id)
    recent_turns = mem["messages"]
    await append_message(session_id, "student", student_message)

    # ---- 1. Diagnostic Agent (sequential, first) ----
    try:
        diag = await asyncio.wait_for(
            diagnostic_agent.run_diagnostic(concept.name, recent_turns, student_message),
            timeout=settings.AGENT_TIMEOUT_SECONDS,
        )
    except (asyncio.TimeoutError, Exception) as e:  # noqa: BLE001
        logger.warning("diagnostic agent timeout/error: %s", e)
        diag = {"confidence": 0.5, "correct_baseline": False}

    # ---- 2. Parallel: Misconception Agent + non-LLM heuristics ----
    async def _misconception():
        try:
            return await asyncio.wait_for(
                misconception_agent.run_misconception_check(concept.name, concept.canonical_facts, student_message),
                timeout=settings.AGENT_TIMEOUT_SECONDS,
            )
        except (asyncio.TimeoutError, Exception) as e:  # noqa: BLE001
            logger.warning("misconception agent timeout/error: %s", e)
            return {"misconception": False, "confidence": 0.0}

    misconception_result = await _misconception()

    prior_lens = [len(t["content"].split()) for t in recent_turns if t["role"] == "student"]
    prior_avg = sum(prior_lens) / len(prior_lens) if prior_lens else 0
    hedge_freq = heuristics.hedge_word_frequency(student_message)
    stuck = heuristics.is_stuck_signal(student_message)
    overload = heuristics.overload_flag(student_message, prior_avg, session.unresolved_turns)
    curiosity = heuristics.curiosity_score(student_message)
    confidence = heuristics.aggregate_confidence(
        self_rated=diag.get("confidence", 0.5),
        hedge_freq=hedge_freq,
        recent_correct_ratio=1.0 if diag.get("correct_baseline") else 0.5,
    )

    signals = Signals(
        confidence=confidence,
        misconception_flag=bool(misconception_result.get("misconception")),
        overload_flag=overload,
        reasoning_steps=2 if len(student_message.split()) > 25 and not stuck else 0,
        stuck=stuck,
        contradiction=bool(misconception_result.get("misconception")),
        curiosity_score=curiosity,
        transfer_solved=False,  # set true via mastery flow / explicit assessment endpoint
        coherent_teach_back=False,
        correct_baseline=bool(diag.get("correct_baseline")),
        shared_ai_usage=bool(diag.get("shared_ai_usage")),
    )

    # ---- 3. Orchestrator: state machine + mode selector ----
    prev_state = LearnerState(session.current_state)
    new_state, unresolved = transition(prev_state, session.unresolved_turns, signals)
    mode = select_mode(new_state, signals, user_selected_mode, domain=concept.domain)

    new_tier = next_tier(session.hint_tier, signals.stuck)
    hint_instr = tier_instruction(new_tier)

    # ---- 4. Socratic Questioning Agent ----
    try:
        tutor_message = await asyncio.wait_for(
            socratic_agent.generate_response(mode, concept.name, recent_turns, student_message, hint_instr),
            timeout=settings.AGENT_TIMEOUT_SECONDS,
        )
    except (asyncio.TimeoutError, Exception) as e:  # noqa: BLE001
        logger.warning("socratic agent timeout/error: %s", e)
        tutor_message = FALLBACK_LLM_UNAVAILABLE

    # ---- 5. Answer-Leak Guard (final gate, max 1 retry then fallback template) ----
    try:
        leaked, reason = await check_leak(tutor_message)
    except Exception as e:  # noqa: BLE001
        logger.warning("leak guard error: %s", e)
        leaked, reason = False, ""
    leak_triggered = leaked
    if leaked:
        logger.info("leak guard triggered: %s", reason)
        corrective = "You just gave away the answer. Rephrase your last message as a guiding question instead."
        try:
            tutor_message = await asyncio.wait_for(
                socratic_agent.generate_response(
                    mode, concept.name, recent_turns, student_message, hint_instr, corrective=corrective
                ),
                timeout=settings.AGENT_TIMEOUT_SECONDS,
            )
            leaked_again, _ = await check_leak(tutor_message)
            if leaked_again:
                tutor_message = FALLBACK_HINT_TEMPLATE
        except (asyncio.TimeoutError, Exception) as e:  # noqa: BLE001
            logger.warning("socratic agent retry timeout/error: %s", e)
            tutor_message = FALLBACK_HINT_TEMPLATE

    db.add(HintLog(
        session_id=session.id,
        tier=new_tier,
        content_hash=hashlib.sha256(tutor_message.encode()).hexdigest()[:16],
        was_leak_flagged=leak_triggered,
    ))

    # ---- 6. Persist turns ----
    db.add(SessionTurn(session_id=session.id, role="student", content=student_message,
                        mode=mode, hint_tier=new_tier, learner_state=new_state.value))
    db.add(SessionTurn(session_id=session.id, role="tutor", content=tutor_message,
                        mode=mode, hint_tier=new_tier, learner_state=new_state.value))

    session.current_state = new_state.value
    session.current_mode = mode
    session.hint_tier = new_tier
    session.unresolved_turns = unresolved
    db.add(session)
    await db.commit()

    await append_message(session_id, "tutor", tutor_message)

    return {
        "tutor_message": tutor_message,
        "learner_state": new_state.value,
        "mode": mode,
        "hint_tier": new_tier,
        "leak_guard_triggered": leak_triggered,
    }


async def run_mastery_check(concept_name: str, evidence: dict) -> dict:
    """Invoked only on state transitions into APPLYING/REFLECTING (cost control,
    Section 11.5) — call explicitly from the reflection/assessment routers."""
    return await mastery_agent.assess_mastery(concept_name, evidence)
