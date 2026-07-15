import logging

logger = logging.getLogger("adaptive_engine")

def get_dynamic_difficulty(user_profile, session_state):
    """
    Adjusts the difficulty scale based on the SemanticMemory's dependency trend
    and the current session's state.
    """
    if user_profile and user_profile.dependency_trend_score:
        if user_profile.dependency_trend_score > 0.7:
            # High dependency: provide less direct help, focus on scaffolding
            return "strict"
    return "balanced"
