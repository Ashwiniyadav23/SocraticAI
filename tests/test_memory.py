import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.memory import ShortTermMemoryManager, WorkingMemoryManager, EpisodicMemoryManager, SemanticMemoryManager
from app.models import User

@pytest.fixture
async def setup_user(db_session: AsyncSession):
    user = User(email=f"test_{uuid.uuid4()}@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.mark.asyncio
async def test_short_term_memory(db_session: AsyncSession):
    thread_id = str(uuid.uuid4())
    checkpoint_id = "cp-1"
    state = {"turn": 1, "messages": ["hello"]}
    
    await ShortTermMemoryManager.save_checkpoint(db_session, thread_id, checkpoint_id, state)
    
    fetched = await ShortTermMemoryManager.get_checkpoint(db_session, thread_id, checkpoint_id)
    assert fetched == state
    
    fetched_none = await ShortTermMemoryManager.get_checkpoint(db_session, thread_id, "non-existent")
    assert fetched_none is None

@pytest.mark.asyncio
async def test_working_memory(db_session: AsyncSession, setup_user):
    user_id = setup_user.id
    
    # Test initial fetch
    mem = await WorkingMemoryManager.hydrate(db_session, user_id)
    assert mem is None
    
    # Test flush (create)
    concepts = ["recursion", "stack"]
    await WorkingMemoryManager.flush(db_session, user_id, concepts)
    
    mem = await WorkingMemoryManager.hydrate(db_session, user_id)
    assert mem is not None
    assert mem.active_concepts == concepts
    assert mem.current_learning_objective_id is None
    
    # Test flush (update)
    new_concepts = ["recursion"]
    obj_id = uuid.uuid4()
    await WorkingMemoryManager.flush(db_session, user_id, new_concepts, obj_id)
    
    mem = await WorkingMemoryManager.hydrate(db_session, user_id)
    assert mem.active_concepts == new_concepts
    assert mem.current_learning_objective_id == obj_id

@pytest.mark.asyncio
async def test_semantic_memory(db_session: AsyncSession, setup_user):
    user_id = setup_user.id
    
    mem = await SemanticMemoryManager.get_dna(db_session, user_id)
    assert mem is None
    
    traits = {
        "learning_style": {"visual": 0.8},
        "strong_topics": ["python"],
        "language_preference": "spanish"
    }
    
    await SemanticMemoryManager.update_dna(db_session, user_id, traits)
    mem = await SemanticMemoryManager.get_dna(db_session, user_id)
    
    assert mem.learning_style == {"visual": 0.8}
    assert mem.strong_topics == ["python"]
    assert mem.language_preference == "spanish"
    assert mem.explanation_style is None

@pytest.mark.asyncio
async def test_episodic_memory(db_session: AsyncSession, setup_user):
    user_id = setup_user.id
    
    embedding = [0.1] * 1536  # Mock 1536-dim embedding
    
    event = await EpisodicMemoryManager.log_event(
        db_session, 
        user_id, 
        "breakthrough", 
        "Understood base cases", 
        {"context": "recursion"}, 
        embedding
    )
    
    assert event.id is not None
    assert event.event_type == "breakthrough"
    
    # Search episodes
    query_embedding = [0.11] * 1536
    
    # Mock search functionality if not supported by sqlite
    # If SQLite fails with cosine distance, we catch it or we just test insert
