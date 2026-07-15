import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import LearnerProfile
from app.ai.graphs.dna_graph import dna_graph

logger = logging.getLogger("dna_engine")

async def update_learning_dna(db: AsyncSession, user_id: uuid.UUID, session_metrics: dict) -> LearnerProfile:
    """
    Updates the LearnerProfile (Learning DNA) based on session telemetry.
    Expected metrics: curiosity_score, ai_dependency_signals, consistency_score, etc.
    """
    profile = await db.get(LearnerProfile, user_id)
    if not profile:
        profile = LearnerProfile(user_id=user_id)
        db.add(profile)
    
    state_input = {
        "session_metrics": session_metrics,
        "current_persona": profile.persona_classification,
        "current_dependency": profile.dependency_trend_score
    }
    
    result = await dna_graph.ainvoke(state_input)
    
    profile.persona_classification = result["new_persona"]
    profile.dependency_trend_score = result["new_dependency"]
    
    logger.info("Updated Learning DNA for user %s: persona=%s, dependency=%.2f", 
                user_id, profile.persona_classification, profile.dependency_trend_score)
    
    await db.commit()
    await db.refresh(profile)
    return profile
