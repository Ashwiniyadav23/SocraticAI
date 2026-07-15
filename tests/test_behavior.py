from app.ai.state_manager import Signals, LearnerState, transition
from app.hint_ladder import next_tier

def test_diagnosis_before_teaching():
    signals = Signals(confidence=0.3, misconception_flag=False, stuck=False, contradiction=False, correct_baseline=False, shared_ai_usage=False)
    state, unres = transition(LearnerState.DIAGNOSING, 0, signals)
    assert state == LearnerState.DIAGNOSING

def test_hint_ladder_progression():
    assert next_tier(0, True) == 1
    assert next_tier(1, True) == 2
    assert next_tier(1, False) == 0

def test_ai_dependency_reduction():
    signals = Signals(confidence=0.9, misconception_flag=False, stuck=False, contradiction=False, correct_baseline=True, shared_ai_usage=True)
    state, unres = transition(LearnerState.RETENTION, 0, signals)
    assert state == LearnerState.INDEPENDENT
