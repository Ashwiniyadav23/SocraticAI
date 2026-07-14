import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import Concept, LearningSession, User
from app.orchestrator import run_turn
from app.schemas import SessionCreate, SessionOut, StateOut, TurnCreate, TurnOut

router = APIRouter(prefix="/v1/session", tags=["session"])


async def _get_or_create_concept(db: AsyncSession, name: str) -> Concept:
    result = await db.execute(select(Concept).where(Concept.name == name))
    concept = result.scalar_one_or_none()
    if not concept:
        concept = Concept(name=name, domain="dsa", prerequisites=[], canonical_facts={})
        db.add(concept)
        await db.commit()
        await db.refresh(concept)
    return concept


@router.post("", response_model=SessionOut)
async def start_session(payload: SessionCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """FR: start a learning session for a concept. Rate limit 20/min/user (Section 19) —
    enforce at the gateway/proxy layer in production; see README."""
    concept = await _get_or_create_concept(db, payload.concept_name)
    session = LearningSession(user_id=user.id, concept_id=concept.id, current_state="UNKNOWN")
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.post("/{session_id}/turn", response_model=TurnOut)
async def post_turn(
    session_id: uuid.UUID,
    payload: TurnCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a student message, get the tutor's Socratic response.
    NOTE: PRD specifies this should stream over WebSocket for perceived
    latency (Section 21 NFR). This is the simple synchronous version —
    see routers/ws_router.py for the streaming variant."""
    session = await db.get(LearningSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    concept = await db.get(Concept, session.concept_id)

    result = await run_turn(db, session, concept, payload.message)
    return TurnOut(session_id=session.id, **result)


@router.get("/{session_id}/state", response_model=StateOut)
async def get_state(session_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    session = await db.get(LearningSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    return StateOut(
        session_id=session.id,
        learner_state=session.current_state,
        mode=session.current_mode,
        hint_tier=session.hint_tier,
    )
