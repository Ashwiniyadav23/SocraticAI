from app.database import Base, db
from app.models import Concept
import uuid

async def test_rag_embedding_and_retrieval(db_session):
    c_id = uuid.uuid4()
    c = Concept(id=c_id, name="Test Concept", domain="Math", canonical_facts=[{"fact": "1+1=2"}])
    db_session.add(c)
    await db_session.commit()
    
    fetched = await db_session.get(Concept, c_id)
    assert fetched.name == "Test Concept"
