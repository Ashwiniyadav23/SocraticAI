from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import Mastery, User
from app.schemas import MasteryOut

router = APIRouter(prefix="/v1/profile", tags=["profile"])


@router.get("/mastery", response_model=list[MasteryOut])
async def get_mastery(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """FR-05: dependency trend + mastery scores across concepts."""
    result = await db.execute(select(Mastery).where(Mastery.user_id == user.id))
    return result.scalars().all()
