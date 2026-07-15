from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import Concept, Mastery, Reflection, User
from app.ai.orchestrator import run_mastery_check
from app.schemas import ReflectionCreate

router = APIRouter(prefix="/v1/reflection", tags=["reflection"])


@router.post("")
async def submit_reflection(payload: ReflectionCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Submit teach-back text. Triggers Mastery Assessment Agent (Section 11.4),
    invoked only at this state-transition moment, not every turn (cost control)."""
    result = await db.execute(select(Concept).where(Concept.name == payload.concept_name))
    concept = result.scalar_one_or_none()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    db.add(Reflection(user_id=user.id, concept_id=concept.id, teach_back_text=payload.teach_back_text))

    assessment = await run_mastery_check(concept.name, {"teach_back_text": payload.teach_back_text})

    m_result = await db.execute(
        select(Mastery).where(Mastery.user_id == user.id, Mastery.concept_id == concept.id)
    )
    mastery = m_result.scalar_one_or_none()
    if not mastery:
        mastery = Mastery(user_id=user.id, concept_id=concept.id)
    mastery.mastery_score = assessment["mastery_score"]
    mastery.evidence_breakdown = assessment["evidence_breakdown"]
    db.add(mastery)
    await db.commit()

    return {
        "mastery_score": assessment["mastery_score"],
        "eligible_for_mastered": assessment["eligible_for_mastered"],
        "weak_areas": assessment.get("weak_areas", []),
    }
