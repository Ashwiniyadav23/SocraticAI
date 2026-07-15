import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import SemanticMemory

class SemanticMemoryManager:
    @staticmethod
    async def get_dna(db: AsyncSession, user_id: uuid.UUID) -> SemanticMemory | None:
        result = await db.execute(select(SemanticMemory).where(SemanticMemory.user_id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_dna(db: AsyncSession, user_id: uuid.UUID, traits: dict) -> SemanticMemory:
        result = await db.execute(select(SemanticMemory).where(SemanticMemory.user_id == user_id))
        mem = result.scalar_one_or_none()
        if not mem:
            mem = SemanticMemory(user_id=user_id)
            db.add(mem)
        
        for key, value in traits.items():
            if hasattr(mem, key) and key != "user_id":
                setattr(mem, key, value)
                
        await db.commit()
        await db.refresh(mem)
        return mem
