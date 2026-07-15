from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import ShortTermMemory

class ShortTermMemoryManager:
    @staticmethod
    async def get_checkpoint(db: AsyncSession, thread_id: str, checkpoint_id: str) -> dict | None:
        result = await db.execute(
            select(ShortTermMemory).where(
                ShortTermMemory.thread_id == thread_id,
                ShortTermMemory.checkpoint_id == checkpoint_id
            )
        )
        record = result.scalar_one_or_none()
        return record.state if record else None

    @staticmethod
    async def save_checkpoint(db: AsyncSession, thread_id: str, checkpoint_id: str, state: dict) -> None:
        mem = ShortTermMemory(
            thread_id=thread_id,
            checkpoint_id=checkpoint_id,
            state=state
        )
        db.add(mem)
        await db.commit()
