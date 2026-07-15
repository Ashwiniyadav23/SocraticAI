from app.ai.context.models import LearningContext
from typing import TypedDict, Any

class PedagogyConfig(TypedDict):
    tutor_mode_override: str | None
    hint_strategy: str
    suppress_curiosity: bool
    resource_recommendation: str | None

def adapt_pedagogy(context: LearningContext) -> PedagogyConfig:
    """
    Translates the LearningContext into configuration settings for Tutor Mode and Hint Strategy.
    """
    config: PedagogyConfig = {
        "tutor_mode_override": None,
        "hint_strategy": "balanced",
        "suppress_curiosity": False,
        "resource_recommendation": None
    }
    
    # Purpose overrides
    purpose = context.purpose.lower()
    if "exam" in purpose:
        config["tutor_mode_override"] = "socratic_assessor"
        config["resource_recommendation"] = "cheat_sheets"
    elif "curiosity" in purpose:
        config["tutor_mode_override"] = "exploratory_guide"
    elif "project" in purpose or "assignment" in purpose:
        config["resource_recommendation"] = "documentation"
    elif "interview" in purpose:
        config["tutor_mode_override"] = "mock_interviewer"
        
    # Urgency overrides
    urgency = context.urgency.lower()
    if urgency == "high":
        config["hint_strategy"] = "direct"
        config["suppress_curiosity"] = True
    elif urgency == "low":
        config["hint_strategy"] = "deep_socratic"
        
    return config
