from dataclasses import dataclass
from typing import Any

from app.ai import behavior_engine as heuristics
from app.ai.state_manager import LearnerState, Signals, transition
from app.hint_ladder import next_tier
from app.mode_selector import select_mode

@dataclass
class SynthesisState:
    signals: Signals
    new_state: str
    new_tier: int
    unresolved: int
    mode: str
    student_message: str
    concept_name: str
    recent_turns: list[dict]
    diag: dict
    misc: dict
    learning_context: dict | None


def synthesize_state(state: dict[str, Any]) -> SynthesisState:
    """
    Hydrates raw input from context loaders into deterministic behavior signals
    and state machine transitions for the ADES policy evaluator.
    """
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

    return SynthesisState(
        signals=signals,
        new_state=new_state_enum.value,
        new_tier=new_tier,
        unresolved=unresolved,
        mode=mode,
        student_message=student_message,
        concept_name=state["concept_name"],
        recent_turns=state["recent_turns"],
        diag=diag,
        misc=misc,
        learning_context=state.get("learning_context")
    )
