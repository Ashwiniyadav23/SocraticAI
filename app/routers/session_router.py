import uuid

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import Concept, LearningSession, User
from app.ai.orchestrator import run_turn
from app.agents.topic_agent import extract_topic
from app.schemas import SessionCreate, SessionOut, StateOut, TurnCreate, TurnOut
from app.ai.context.models import LearningContext
from app.models import SessionContext

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

from app.database import get_db, db as db_manager

async def _extract_and_update_topic(session_id: uuid.UUID, message: str):
    """Background task to extract topic from first message and update the session."""
    topic = await extract_topic(message)
    if topic != "General Inquiry":
        async with db_manager.session_maker() as db:
            concept = await _get_or_create_concept(db, topic)
            session = await db.get(LearningSession, session_id)
            if session:
                session.concept_id = concept.id
                await db.commit()

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

@router.post("/auto", response_model=SessionOut)
async def start_session_auto(payload: TurnCreate, background_tasks: BackgroundTasks, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Auto-starts a session with 'General Inquiry' and triggers background topic extraction."""
    concept = await _get_or_create_concept(db, "General Inquiry")
    session = LearningSession(user_id=user.id, concept_id=concept.id, current_state="UNKNOWN")
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    # Schedule background topic extraction
    background_tasks.add_task(_extract_and_update_topic, session.id, payload.message)
    
    return session

@router.post("/{session_id}/turn", response_model=TurnOut)
async def post_turn(
    session_id: uuid.UUID,
    payload: TurnCreate,
    background_tasks: BackgroundTasks,
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

    result = await run_turn(db, session, concept, payload.message, background_tasks=background_tasks)
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


@router.post("/{session_id}/context", response_model=LearningContext)
async def set_context(session_id: uuid.UUID, payload: LearningContext, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    session = await db.get(LearningSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Session not found")
        
    context_entry = SessionContext(
        session_id=session.id,
        purpose=payload.purpose,
        urgency=payload.urgency,
        deadline=None, # date parsing if string passed
        expected_depth=payload.expected_depth,
        objective=payload.objective
    )
    if payload.deadline:
        from datetime import datetime
        try:
            context_entry.deadline = datetime.fromisoformat(payload.deadline)
        except ValueError:
            pass
            
    db.add(context_entry)
    await db.commit()
    await db.refresh(context_entry)
    
    session.context_id = context_entry.id
    await db.commit()
    
    return payload


@router.get("/{session_id}/context", response_model=LearningContext)
async def get_context(session_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    session = await db.get(LearningSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if not session.context_id:
        raise HTTPException(status_code=404, detail="Context not found")
        
    context_entry = await db.get(SessionContext, session.context_id)
    return LearningContext(
        purpose=context_entry.purpose,
        urgency=context_entry.urgency,
        deadline=context_entry.deadline.isoformat() if context_entry.deadline else None,
        expected_depth=context_entry.expected_depth,
        objective=context_entry.objective
    )
