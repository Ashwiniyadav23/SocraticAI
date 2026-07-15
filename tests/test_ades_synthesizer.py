from app.ai.decision_engine.synthesizer import synthesize_state
from app.ai.state_manager import LearnerState

def test_synthesizer_hydration():
    raw_state = {
        "concept_name": "Recursion",
        "concept_domain": "dsa",
        "recent_turns": [],
        "student_message": "I don't know this at all, it's so frustrating and I'm totally lost.",
        "session_unresolved_turns": 2,
        "session_hint_tier": 0,
        "session_current_state": "CONFUSED",
        "user_selected_mode": None,
        "diag": {"confidence": 0.1, "correct_baseline": False, "shared_ai_usage": False},
        "misconception_result": {"misconception": True}
    }
    
    synth = synthesize_state(raw_state)
    
    assert synth.student_message == raw_state["student_message"]
    assert synth.signals.stuck is True
    assert synth.signals.misconception_flag is True
    assert synth.new_state == LearnerState.SCAFFOLDED.value
