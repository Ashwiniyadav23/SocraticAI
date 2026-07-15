import uuid
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import EducationalDocumentChunk
from app.ai.model_router import get_embedding

async def ingest_document(db: AsyncSession, doc_id: str, topic: str, chunks: list[dict[str, Any]]):
    """
    Ingest a list of chunks for a document.
    chunks format: [{"text": "...", "difficulty_level": 1, "format": "Text", "language": "English", "metadata": {}}]
    """
    for chunk in chunks:
        embedding = await get_embedding(chunk["text"])
        doc_chunk = EducationalDocumentChunk(
            document_id=doc_id,
            topic=topic,
            difficulty_level=chunk.get("difficulty_level", 3),
            format=chunk.get("format", "Text"),
            language=chunk.get("language", "English"),
            text=chunk["text"],
            embedding=embedding,
            source_metadata=chunk.get("metadata", {})
        )
        db.add(doc_chunk)
    await db.commit()
