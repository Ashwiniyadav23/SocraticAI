import uuid
import logging
from sqlalchemy import select
from app.database import db
from app.models import LearnerProfile
from app.ai.graphs.dna_graph import dna_graph

logger = logging.getLogger("event_bus")

async def trigger_dna_update(user_id: uuid.UUID, signals_dict: dict):
    """
    Background task to update the longitudinal LearnerProfile
    based on signals from the latest conversation turn.
    """
    try:
        async with db.session_maker() as session:
            # Fetch profile
            result = await session.execute(
                select(LearnerProfile).where(LearnerProfile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()
            if not profile:
                logger.warning(f"No LearnerProfile found for user {user_id}")
                return

            state_input = {
                "session_metrics": signals_dict,
                "current_persona": profile.persona_classification,
                "current_dependency": profile.dependency_trend_score,
                "new_persona": None,
                "new_dependency": None
            }

            result_state = await dna_graph.ainvoke(state_input)

            profile.persona_classification = result_state["new_persona"]
            profile.dependency_trend_score = result_state["new_dependency"]
            session.add(profile)
            await session.commit()
            logger.info(f"DNA updated for user {user_id}: persona={profile.persona_classification}, dependency={profile.dependency_trend_score:.2f}")

    except Exception as e:
        logger.error(f"Failed to update DNA for user {user_id}: {e}")
