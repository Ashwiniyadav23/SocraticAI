import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import Base, db, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.pool import NullPool
from app.config import settings
import pytest_asyncio
import pytest

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session", autouse=True)
def init_test_db_sync():
    from sqlalchemy import create_engine
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
    if sync_url.startswith("postgresql://"):
        # Ensure it uses psycopg2 which is default for sync postgresql in SQLAlchemy
        pass
    engine = create_engine(sync_url)
    Base.metadata.drop_all(engine)
    
    # Need to create vector extension
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest_asyncio.fixture(autouse=True)
async def inject_db_engine():
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    db.engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    db.session_maker = async_sessionmaker(db.engine, expire_on_commit=False, class_=AsyncSession)
    
    # Mock db.init and db.close to prevent lifespan from overwriting the test engine
    original_init = db.init
    original_close = db.close
    db.init = lambda url: None
    async def fake_close():
        pass
    db.close = fake_close
    
    yield
    
    db.init = original_init
    db.close = original_close
    await db.engine.dispose()

@pytest_asyncio.fixture
async def db_connection(inject_db_engine):
    # Get a single connection for the test
    async with db.engine.connect() as conn:
        yield conn

@pytest_asyncio.fixture
async def db_session(db_connection):
    # Start a transaction on the connection
    trans = await db_connection.begin()
    # Create a savepoint
    nested = await db_connection.begin_nested()
    
    async_session = AsyncSession(bind=db_connection, expire_on_commit=False, join_transaction_mode="create_savepoint")
    yield async_session
    await async_session.close()
    
    if nested.is_active:
        await nested.rollback()
    await trans.rollback()

@pytest_asyncio.fixture
async def client(db_session):
    # Override get_db to return the exact same test transaction
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
