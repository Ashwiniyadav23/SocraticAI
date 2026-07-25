import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_mentor
from app.database import get_db
from app.models import AnalyticsEvent, Concept, Mastery, User
from app.schemas import MentorOverride

router = APIRouter(prefix="/v1/mentor", tags=["mentor"])


@router.get("/students")
async def list_students(mentor: User = Depends(require_mentor), db: AsyncSession = Depends(get_db)):
    from app.models import SemanticMemory
    result = await db.execute(select(User).where(User.role == "student"))
    students = result.scalars().all()
    out = []
    for s in students:
        m_result = await db.execute(select(Mastery).where(Mastery.user_id == s.id))
        masteries = m_result.scalars().all()
        
        sem_mem_result = await db.execute(select(SemanticMemory).where(SemanticMemory.user_id == s.id))
        sem_mem = sem_mem_result.scalar_one_or_none()
        
        traits = sem_mem.behavioral_traits if sem_mem else {}
        
        out.append({
            "student_id": s.id,
            "email": s.email,
            "mastery_summary": [{"concept_id": m.concept_id, "score": m.mastery_score} for m in masteries],
            "confidence": traits.get("confidence", 0.5),
            "ai_dependency": traits.get("ai_dependency", 0.5),
            "curiosity_score": traits.get("curiosity_score", 0.5),
            "independent_thinking": traits.get("independent_thinking", 0.5),
            "learning_velocity": traits.get("learning_velocity", 0.5),
            "weak_concepts": sem_mem.weak_topics if sem_mem else [],
            "strong_concepts": sem_mem.strong_topics if sem_mem else [],
        })
    return out


@router.post("/override")
async def override_mode(payload: MentorOverride, mentor: User = Depends(require_mentor), db: AsyncSession = Depends(get_db)):
    """Mentor authority > AI (Section 15). Logged and takes precedence for
    that student/concept going forward — persisted as an analytics event that
    the orchestrator's mode selector should be extended to check first
    (left as a TODO hook: see README 'Extending the orchestrator')."""
    result = await db.execute(select(Concept).where(Concept.name == payload.concept_name))
    concept = result.scalar_one_or_none()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    db.add(AnalyticsEvent(
        user_id=payload.student_id,
        event_type="mentor_override",
        payload={"concept_id": str(concept.id), "forced_mode": payload.forced_mode, "mentor_id": str(mentor.id)},
    ))
    await db.commit()
    return {"status": "override_recorded"}
