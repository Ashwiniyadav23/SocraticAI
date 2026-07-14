"""
Learner State Machine — implemented as deterministic code, not prompts
(PRD Section 11.5: "not subject to LLM drift"). Mirrors Section 8.
"""
from enum import StrEnum


class LearnerState(StrEnum):
    UNKNOWN = "UNKNOWN"
    DIAGNOSING = "DIAGNOSING"
    EXPLORING = "EXPLORING"
    CONFUSED = "CONFUSED"
    REASONING = "REASONING"
    SCAFFOLDED = "SCAFFOLDED"
    APPLYING = "APPLYING"
    REFLECTING = "REFLECTING"
    MASTERED = "MASTERED"
    RETENTION = "RETENTION"
    INDEPENDENT = "INDEPENDENT"


class Signals:
    """Behavioral signals extracted for the current turn (Section 8)."""

    def __init__(
        self,
        confidence: float = 0.5,
        misconception_flag: bool = False,
        overload_flag: bool = False,
        reasoning_steps: int = 0,
        stuck: bool = False,
        contradiction: bool = False,
        curiosity_score: float = 0.0,
        transfer_solved: bool = False,
        coherent_teach_back: bool = False,
        correct_baseline: bool = False,
        shared_ai_usage: bool = False,
    ):
        self.confidence = confidence
        self.misconception_flag = misconception_flag
        self.overload_flag = overload_flag
        self.reasoning_steps = reasoning_steps
        self.stuck = stuck
        self.contradiction = contradiction
        self.curiosity_score = curiosity_score
        self.transfer_solved = transfer_solved
        self.coherent_teach_back = coherent_teach_back
        self.correct_baseline = correct_baseline
        self.shared_ai_usage = shared_ai_usage


def transition(state: LearnerState, unresolved_turns: int, signals: Signals) -> tuple[LearnerState, int]:
    """Applies the condensed decision table from Section 8.
    Returns (new_state, new_unresolved_turns)."""

    s = state

    if s == LearnerState.UNKNOWN:
        return LearnerState.DIAGNOSING, 0

    if s == LearnerState.DIAGNOSING:
        if signals.correct_baseline:
            return LearnerState.EXPLORING, 0
        if signals.stuck:
            return LearnerState.CONFUSED, unresolved_turns + 1
        return s, unresolved_turns

    if s == LearnerState.EXPLORING:
        if signals.contradiction:
            return LearnerState.CONFUSED, unresolved_turns  # misconception flag routes mode, not just state
        if signals.reasoning_steps >= 2:
            return LearnerState.REASONING, 0
        return s, unresolved_turns

    if s == LearnerState.CONFUSED:
        if unresolved_turns + 1 >= 2:
            return LearnerState.SCAFFOLDED, unresolved_turns + 1
        return s, unresolved_turns + (1 if signals.stuck else 0)

    if s == LearnerState.SCAFFOLDED:
        if not signals.stuck:
            return LearnerState.REASONING, 0
        return s, unresolved_turns + 1  # 3rd consecutive -> escalate hint tier (handled by caller)

    if s == LearnerState.REASONING:
        if signals.transfer_solved:  # "solution outline correct" proxy
            return LearnerState.APPLYING, 0
        if signals.contradiction:
            return LearnerState.CONFUSED, 0
        return s, unresolved_turns

    if s == LearnerState.APPLYING:
        if signals.transfer_solved:
            return LearnerState.REFLECTING, 0
        return s, unresolved_turns

    if s == LearnerState.REFLECTING:
        if signals.coherent_teach_back:
            return LearnerState.MASTERED, 0
        return s, unresolved_turns

    if s == LearnerState.MASTERED:
        return LearnerState.RETENTION, 0  # scheduler-driven in practice; see routers/mentor or a cron job

    if s == LearnerState.RETENTION:
        if signals.correct_baseline:
            return LearnerState.INDEPENDENT, 0
        return LearnerState.SCAFFOLDED, 0

    return s, unresolved_turns
