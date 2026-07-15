import pytest
from app.ai.decision_engine.policy_rules import evaluate_policy
from app.ai.decision_engine.synthesizer import SynthesisState
from app.ai.state_manager import Signals, LearnerState

@pytest.mark.asyncio
async def test_policy_overload_heuristic():
    signals = Signals(
        confidence=0.1, misconception_flag=False, overload_flag=True, 
        reasoning_steps=0, stuck=True, contradiction=False, curiosity_score=0.0,
        transfer_solved=False, coherent_teach_back=False, correct_baseline=False,
        shared_ai_usage=False
    )
    synth = SynthesisState(
        signals=signals, new_state=LearnerState.CONFUSED.value,
        new_tier=2, unresolved=3, mode="socratic_tutor", student_message="I quit",
        concept_name="Arrays", recent_turns=[], diag={}, misc={}, learning_context=None
    )
    
    decision = await evaluate_policy(synth)
    assert decision.target_node == "mentor_intervention"
    assert decision.tutor_mode == "mentor"
    assert "empathy" in decision.constraints

@pytest.mark.asyncio
async def test_policy_reflection_heuristic():
    signals = Signals(
        confidence=0.9, misconception_flag=False, overload_flag=False, 
        reasoning_steps=2, stuck=False, contradiction=False, curiosity_score=0.0,
        transfer_solved=True, coherent_teach_back=False, correct_baseline=True,
        shared_ai_usage=False
    )
    synth = SynthesisState(
        signals=signals, new_state=LearnerState.REFLECTING.value,
        new_tier=0, unresolved=0, mode="socratic_tutor", student_message="Got it!",
        concept_name="Arrays", recent_turns=[], diag={}, misc={}, learning_context=None
    )
    
    decision = await evaluate_policy(synth)
    assert decision.target_node == "reflection"
    assert decision.tutor_mode == "evaluator"
