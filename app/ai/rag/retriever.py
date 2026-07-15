from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import EducationalDocumentChunk
from app.ai.model_router import get_embedding

async def retrieve_chunks(db: AsyncSession, query: str, topic: str | None = None, difficulty: int | None = None, top_k: int = 10) -> list[EducationalDocumentChunk]:
    """
    Retrieves the most semantically similar chunks, optionally pre-filtered by topic and difficulty.
    Uses pgvector's L2 distance (cosine_distance is <-> but pgvector supports multiple). We use <=> for cosine distance.
    """
    query_embedding = await get_embedding(query)
    
    stmt = select(EducationalDocumentChunk)
    if topic:
        stmt = stmt.where(EducationalDocumentChunk.topic == topic)
    if difficulty:
        # allow within 1 level of difficulty
        stmt = stmt.where(EducationalDocumentChunk.difficulty_level.between(max(1, difficulty - 1), min(5, difficulty + 1)))
        
    # cosine distance
    stmt = stmt.order_by(EducationalDocumentChunk.embedding.cosine_distance(query_embedding)).limit(top_k)
    
    result = await db.execute(stmt)
    return list(result.scalars().all())
