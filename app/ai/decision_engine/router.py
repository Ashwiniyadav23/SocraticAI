import json
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import DecisionLog
from app.ai.decision_engine.synthesizer import synthesize_state
from app.ai.decision_engine.policy_rules import evaluate_policy
from app.database import db

async def route_turn(state: dict[str, Any], session_id: str | None = None) -> dict[str, Any]:
    """
    Core ADES Router. Synthesizes inputs, runs policy, logs decision,
    and returns state updates including the selected target node.
    """
    # 1. Synthesize state
    synth_state = synthesize_state(state)
    
    # 2. Evaluate Policy
    decision = await evaluate_policy(synth_state)
    
    # 3. Prepare Snapshot for Logging
    inputs_snapshot = {
        "student_message": synth_state.student_message,
        "signals": vars(synth_state.signals),
        "new_state": synth_state.new_state,
        "mode": synth_state.mode,
        "diag": synth_state.diag,
        "misc": synth_state.misc
    }
    
    decision_output = {
        "target_node": decision.target_node,
        "tutor_mode": decision.tutor_mode,
        "constraints": decision.constraints,
        "reasoning": decision.reasoning
    }
    
    # 4. Log to Database
    if session_id and db.session_maker:
        try:
            async with db.session_maker() as session:
                log_entry = DecisionLog(
                    session_id=session_id,
                    inputs_snapshot=inputs_snapshot,
                    decision_output=decision_output
                )
                session.add(log_entry)
                await session.commit()
        except Exception as e:
            # We don't fail the graph if logging fails, but we should log it internally
            print(f"Error logging decision: {e}")

    # 5. Return updated state to Graph
    return {
        "signals": synth_state.signals,
        "new_state": synth_state.new_state,
        "mode": decision.tutor_mode,
        "new_tier": synth_state.new_tier,
        "unresolved": synth_state.unresolved,
        "target_node": decision.target_node,
        "constraints": decision.constraints
    }
