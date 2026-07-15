from app.database import Base, db
from app.models import User
import uuid

async def test_crud_and_transactions(db_session):
    user_id = uuid.uuid4()
    new_user = User(id=user_id, email="test@example.com", hashed_password="hashed")
    db_session.add(new_user)
    await db_session.commit()
    
    fetched = await db_session.get(User, user_id)
    assert fetched is not None
    assert fetched.email == "test@example.com"

async def test_transaction_rollback(db_session):
    user_id = uuid.uuid4()
    new_user = User(id=user_id, email="rollback@example.com", hashed_password="pwd")
    db_session.add(new_user)
    await db_session.flush()
    await db_session.rollback()
    
    fetched = await db_session.get(User, user_id)
    assert fetched is None

async def test_pgvector_support(db_session):
    from sqlalchemy import text
    result = await db_session.execute(text("SELECT '[1,2,3]'::vector;"))
    assert result.scalar() is not None
