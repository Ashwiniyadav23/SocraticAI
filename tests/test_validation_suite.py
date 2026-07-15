import pytest
import uuid
import asyncio
from datetime import datetime, timezone
import redis.asyncio as redis
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.main import app
from app.config import settings
from app.models import User
from app.ai.memory import (
    ShortTermMemoryManager, WorkingMemoryManager, 
    EpisodicMemoryManager, SemanticMemoryManager
)
from app.ai.memory.manager import set_working_memory, get_working_memory, append_message, get_redis

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def setup_user(db_session: AsyncSession):
    user = User(email=f"validation_{uuid.uuid4()}@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

async def test_step1_and_2_memory_crud_and_isolation(db_session: AsyncSession, setup_user):
    user1 = setup_user
    user2 = User(email=f"validation_{uuid.uuid4()}@example.com")
    db_session.add(user2)
    await db_session.commit()
    
    # 1. Semantic CRUD
    # Create / Update
    await SemanticMemoryManager.update_dna(db_session, user1.id, {"language_preference": "french"})
    await SemanticMemoryManager.update_dna(db_session, user2.id, {"language_preference": "spanish"})
    
    # Read
    fetch1 = await SemanticMemoryManager.get_dna(db_session, user1.id)
    fetch2 = await SemanticMemoryManager.get_dna(db_session, user2.id)
    assert fetch1.language_preference == "french"
    assert fetch2.language_preference == "spanish"
    
    # Isolation
    assert fetch1.user_id != fetch2.user_id
    
    # 2. Working CRUD
    await WorkingMemoryManager.flush(db_session, user1.id, ["arrays"])
    await WorkingMemoryManager.flush(db_session, user2.id, ["pointers"])
    
    w1 = await WorkingMemoryManager.hydrate(db_session, user1.id)
    w2 = await WorkingMemoryManager.hydrate(db_session, user2.id)
    assert w1.active_concepts == ["arrays"]
    assert w2.active_concepts == ["pointers"]

async def test_step3_and_7_pgvector_similarity(db_session: AsyncSession, setup_user):
    user = setup_user
    # Insert episodic memories with vectors
    await EpisodicMemoryManager.log_event(
        db_session, user.id, "breakthrough", "Learned Arrays", {}, [1.0] + [0.0] * 1535
    )
    await EpisodicMemoryManager.log_event(
        db_session, user.id, "breakthrough", "Learned Pointers", {}, [0.0] + [1.0] * 1535
    )
    
    # Search closest to Arrays
    results = await EpisodicMemoryManager.search_episodes(db_session, user.id, [1.0] + [0.0] * 1535, 1)
    assert len(results) == 1
    assert results[0].description == "Learned Arrays"
    
    # Search closest to Pointers
    results2 = await EpisodicMemoryManager.search_episodes(db_session, user.id, [0.0] + [1.0] * 1535, 1)
    assert len(results2) == 1
    assert results2[0].description == "Learned Pointers"

async def test_step5_redis_short_term_memory():
    # Verify Short-Term Memory (conversation history) stored in Redis with TTL
    session_id = str(uuid.uuid4())
    await append_message(session_id, "student", "hello")
    
    mem = await get_working_memory(session_id)
    assert len(mem["messages"]) == 1
    assert mem["messages"][0]["content"] == "hello"
    
    r = get_redis()
    ttl = await r.ttl(f"working:{session_id}")
    assert ttl > 0
    
    # Verify expiration works (by setting TTL to 1 and waiting)
    await r.expire(f"working:{session_id}", 1)
    await asyncio.sleep(1.1)
    expired_mem = await get_working_memory(session_id)
    assert len(expired_mem["messages"]) == 0

async def test_step6_postgresql_verification(db_session: AsyncSession, setup_user):
    user = setup_user
    # Verify Semantic Memory
    dna = await SemanticMemoryManager.update_dna(db_session, user.id, {"explanation_style": "socratic"})
    assert dna.explanation_style == "socratic"
    
    # Working memory (closest to learning journey goals for now in MAS)
    await WorkingMemoryManager.flush(db_session, user.id, ["recursion"])
    wm = await WorkingMemoryManager.hydrate(db_session, user.id)
    assert "recursion" in wm.active_concepts

async def test_step9_regression_endpoints():
    # Verify health
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/health")
        assert resp.status_code == 200
        
        # Test WS or Auth if endpoints exist (basic check)
        auth_resp = await ac.post("/v1/auth/register", json={
            "email": f"test_{uuid.uuid4()}@example.com",
            "password": "password123",
            "role": "student"
        })
        assert auth_resp.status_code in [200, 201]
