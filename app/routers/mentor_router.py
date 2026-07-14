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
    """P2: mentor dashboard - list students + mastery summaries."""
    result = await db.execute(select(User).where(User.role == "student"))
    students = result.scalars().all()
    out = []
    for s in students:
        m_result = await db.execute(select(Mastery).where(Mastery.user_id == s.id))
        masteries = m_result.scalars().all()
        out.append({
            "student_id": s.id,
            "email": s.email,
            "mastery_summary": [{"concept_id": m.concept_id, "score": m.mastery_score} for m in masteries],
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
