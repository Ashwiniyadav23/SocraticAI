"""Mode Selector — Section 9 pseudo-algorithm, implemented as code."""
from app.state_machine import LearnerState, Signals

CURIOSITY_THRESHOLD = 0.5


def select_mode(state: LearnerState, signals: Signals, user_selected: str | None, domain: str) -> str:
    if signals.misconception_flag:
        return "MISCONCEPTION_CORRECTOR"
    if signals.overload_flag:
        return "FOUNDATION_BUILDER"
    if state == LearnerState.CONFUSED and signals.confidence < 0.3:
        return "FOUNDATION_BUILDER"
    if state == LearnerState.SCAFFOLDED:
        return "SCAFFOLDING_COACH"
    if state in (LearnerState.REASONING, LearnerState.EXPLORING) and signals.curiosity_score > CURIOSITY_THRESHOLD:
        return "DEEP_THINKING_PARTNER"
    if state == LearnerState.APPLYING and domain == "code":
        return "IMPLEMENTATION_COACH"
    if state == LearnerState.REFLECTING:
        return "REFLECTION_COACH"
    if user_selected == "interview":
        return "INTERVIEW_MODE"
    return "SOCRATIC_COACH"
