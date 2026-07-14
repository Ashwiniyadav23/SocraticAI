from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Create tables if they don't exist. For MVP we skip Alembic migrations;
    swap to `alembic upgrade head` once the schema stabilizes (see README)."""
    async with engine.begin() as conn:
        from app import models  # noqa: F401  (ensures models are registered)
        await conn.run_sync(Base.metadata.create_all)
