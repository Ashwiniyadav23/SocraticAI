import json
from dataclasses import dataclass
from typing import Any

from app.config import settings
from app.ai.model_router import chat, safe_json_parse
from app.ai.decision_engine.synthesizer import SynthesisState
from app.ai.state_manager import LearnerState
from app.ai.context import LearningContext, adapt_pedagogy

@dataclass
class PolicyDecision:
    target_node: str
    tutor_mode: str
    constraints: dict[str, Any]
    reasoning: str


async def evaluate_policy(state: SynthesisState) -> PolicyDecision:
    """
    Evaluates the SynthesisState against strict heuristic rules first.
    If it falls through the heuristics, invokes the LLM Policy Evaluator.
    """
    base_constraints = {}
    mode_override = None
    
    if state.learning_context:
        ctx = LearningContext(**state.learning_context)
        pedagogy = adapt_pedagogy(ctx)
        if pedagogy["tutor_mode_override"]:
            mode_override = pedagogy["tutor_mode_override"]
        base_constraints["hint_strategy"] = pedagogy["hint_strategy"]
        if pedagogy["suppress_curiosity"]:
            base_constraints["suppress_curiosity"] = True
        if pedagogy["resource_recommendation"]:
            base_constraints["resource_recommendation"] = pedagogy["resource_recommendation"]

    # Rule 1: Extreme Frustration/Overload -> Mentor Intervention
    if state.signals.overload_flag or state.signals.stuck and state.signals.confidence < 0.3:
        return PolicyDecision(
            target_node="mentor_intervention",
            tutor_mode="mentor",
            constraints={"max_length": "short", "empathy": "high"},
            reasoning="Heuristic: Overload or stuck with low confidence detected."
        )

    # Rule 2: Mastery/Reflection Ready -> Trigger Reflection
    if state.new_state in (LearnerState.APPLYING.value, LearnerState.REFLECTING.value):
        # We can route to reflection node for assessing mastery
        return PolicyDecision(
            target_node="reflection",
            tutor_mode="evaluator",
            constraints={"focus": "teach_back"},
            reasoning="Heuristic: Learner transitioned to Applying/Reflecting state."
        )
        
    # Rule 3: Active Misconception -> Socratic with Misconception Mode
    if state.signals.misconception_flag:
        return PolicyDecision(
            target_node="socratic",
            tutor_mode="misconception_tutor", # assumes this mode exists or falls back
            constraints={"focus": "correct_contradiction"},
            reasoning="Heuristic: Contradiction detected in diagnosis."
        )

    # Rule 4: Default Socratic routing if simple
    if not state.signals.stuck and not state.signals.overload_flag:
        return PolicyDecision(
            target_node="socratic",
            tutor_mode=mode_override or state.mode,
            constraints=base_constraints,
            reasoning="Heuristic: Normal learning flow."
        )

    # ---------------------------------------------------------
    # LLM Policy Evaluator for ambiguous cases
    # ---------------------------------------------------------
    system_prompt = (
        "You are the AI Decision Engine routing policy evaluator. "
        "Based on the learner's state, decide the best target node ('socratic', 'mentor_intervention', or 'reflection').\n"
        "Output JSON with keys: 'target_node', 'tutor_mode', 'constraints', 'reasoning'."
    )
    
    context = (
        f"State: {state.new_state}\n"
        f"Signals: {state.signals}\n"
        f"Message: {state.student_message}\n"
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": context}
    ]
    
    try:
        raw = await chat(messages, model=settings.LLM_MODEL_FAST, temperature=0.1, max_tokens=150, json_mode=True)
        parsed = safe_json_parse(raw, {})
        
        target = parsed.get("target_node", "socratic")
        if target not in ["socratic", "mentor_intervention", "reflection"]:
            target = "socratic"
            
        return PolicyDecision(
            target_node=target,
            tutor_mode=mode_override or parsed.get("tutor_mode", state.mode),
            constraints={**base_constraints, **parsed.get("constraints", {})},
            reasoning=f"LLM Policy Evaluator: {parsed.get('reasoning', 'No reasoning provided')}"
        )
    except Exception as e:
        return PolicyDecision(
            target_node="socratic",
            tutor_mode=mode_override or state.mode,
            constraints=base_constraints,
            reasoning=f"LLM Policy Evaluator Failed: {e}"
        )
