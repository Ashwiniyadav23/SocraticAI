import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import EpisodicMemory

class EpisodicMemoryManager:
    @staticmethod
    async def log_event(db: AsyncSession, user_id: uuid.UUID, event_type: str, description: str, context_snapshot: dict, embedding: list[float] | None = None) -> EpisodicMemory:
        mem = EpisodicMemory(
            user_id=user_id,
            event_type=event_type,
            description=description,
            context_snapshot=context_snapshot,
            embedding=embedding
        )
        db.add(mem)
        await db.commit()
        await db.refresh(mem)
        return mem

    @staticmethod
    async def search_episodes(db: AsyncSession, user_id: uuid.UUID, query_embedding: list[float], limit: int = 5) -> list[EpisodicMemory]:
        stmt = (
            select(EpisodicMemory)
            .where(EpisodicMemory.user_id == user_id)
            .where(EpisodicMemory.embedding.is_not(None))
            .order_by(EpisodicMemory.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
