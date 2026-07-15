import pytest
from app.models import EducationalDocumentChunk
from app.ai.rag.ranker import rank_chunks
from app.ai.rag.prompts import rewrite_query
from unittest.mock import patch

def test_ranker_dna_visual():
    chunks = [
        EducationalDocumentChunk(text="text version", format="Text"),
        EducationalDocumentChunk(text="diagram version", format="Diagram"),
    ]
    dna = {"learning_style": {"visual": True}}
    ranked = rank_chunks(chunks, dna, {})
    assert ranked[0].format == "Diagram"

def test_ranker_context_exam():
    chunks = [
        EducationalDocumentChunk(text="diagram version", format="Diagram"),
        EducationalDocumentChunk(text="text version", format="Text"),
    ]
    context = {"purpose": "Exam"}
    ranked = rank_chunks(chunks, None, context)
    assert ranked[0].format == "Text"

def test_ranker_context_interview_high_urgency():
    chunks = [
        EducationalDocumentChunk(text="long explanation", format="Text"),
        EducationalDocumentChunk(text="step by step guide", format="Step-by-Step"),
    ]
    context = {"purpose": "Interview Prep", "urgency": "High"}
    ranked = rank_chunks(chunks, None, context)
    assert ranked[0].format == "Step-by-Step"

@pytest.mark.asyncio
async def test_rewrite_query():
    with patch("app.ai.rag.prompts.chat", return_value="closure javascript advanced"):
        res = await rewrite_query("what is it", ["closures", "scope"], [])
        assert res == "closure javascript advanced"

@pytest.mark.asyncio
async def test_bars_retriever_db(db_session):
    from app.ai.rag.ingestion import ingest_document
    from app.ai.rag.retriever import retrieve_chunks
    from unittest.mock import patch
    
    chunks = [
        {"text": "Advanced topics on Python decorators", "difficulty_level": 5, "format": "Text"},
        {"text": "Beginner guide to Python lists", "difficulty_level": 1, "format": "Step-by-Step"}
    ]
    
    with patch("app.ai.rag.ingestion.get_embedding", return_value=[0.1]*1536):
        await ingest_document(db_session, "doc_1", "Python", chunks)
        
    with patch("app.ai.rag.retriever.get_embedding", return_value=[0.1]*1536):
        # Retrieve with difficulty=5
        res = await retrieve_chunks(db_session, "decorators", topic="Python", difficulty=5)
        assert len(res) == 1
        assert res[0].difficulty_level == 5
        
        # Retrieve with difficulty=1
        res = await retrieve_chunks(db_session, "lists", topic="Python", difficulty=1)
        assert len(res) == 1
        assert res[0].difficulty_level == 1
