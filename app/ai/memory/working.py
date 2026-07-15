import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import WorkingMemory

class WorkingMemoryManager:
    @staticmethod
    async def hydrate(db: AsyncSession, user_id: uuid.UUID) -> WorkingMemory | None:
        result = await db.execute(select(WorkingMemory).where(WorkingMemory.user_id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def flush(db: AsyncSession, user_id: uuid.UUID, active_concepts: list, objective_id: uuid.UUID | None = None) -> None:
        result = await db.execute(select(WorkingMemory).where(WorkingMemory.user_id == user_id))
        mem = result.scalar_one_or_none()
        if not mem:
            mem = WorkingMemory(
                user_id=user_id, 
                active_concepts=active_concepts, 
                current_learning_objective_id=objective_id,
                last_active_at=datetime.now(timezone.utc)
            )
            db.add(mem)
        else:
            mem.active_concepts = active_concepts
            mem.current_learning_objective_id = objective_id
            mem.last_active_at = datetime.now(timezone.utc)
        await db.commit()
