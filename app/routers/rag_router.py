from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.ai.rag.ingestion import ingest_document
from app.ai.rag.retriever import retrieve_chunks
from pydantic import BaseModel

router = APIRouter(prefix="/v1/rag", tags=["rag"])

class IngestPayload(BaseModel):
    document_id: str
    topic: str
    chunks: list[dict]

class QueryPayload(BaseModel):
    query: str
    topic: str | None = None
    difficulty: int | None = None

@router.post("/ingest")
async def ingest_doc(payload: IngestPayload, db: AsyncSession = Depends(get_db)):
    await ingest_document(db, payload.document_id, payload.topic, payload.chunks)
    return {"status": "success", "chunks_ingested": len(payload.chunks)}

@router.post("/query")
async def query_doc(payload: QueryPayload, db: AsyncSession = Depends(get_db)):
    chunks = await retrieve_chunks(db, payload.query, payload.topic, payload.difficulty)
    return {"results": [{"text": c.text, "format": c.format, "difficulty": c.difficulty_level} for c in chunks]}
