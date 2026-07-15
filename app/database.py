from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from app.config import settings

class Base(DeclarativeBase):
    pass

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.session_maker = None

    def init(self, db_url: str):
        self.engine = create_async_engine(db_url, echo=False, future=True)
        self.session_maker = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

    async def close(self):
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.session_maker = None

db = DatabaseManager()

async def get_db():
    if not db.session_maker:
        raise RuntimeError("Database not initialized. Call db.init() in lifespan.")
    async with db.session_maker() as session:
        yield session

async def init_db():
    """Create tables if they don't exist. For MVP we skip Alembic migrations;
    swap to `alembic upgrade head` once the schema stabilizes (see README)."""
    if not db.engine:
        raise RuntimeError("Database not initialized.")
    async with db.engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        from app import models  # noqa: F401  (ensures models are registered)
        await conn.run_sync(Base.metadata.create_all)
