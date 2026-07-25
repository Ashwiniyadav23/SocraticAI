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

async def seed_default_admin():
    """Seed default administrator account automatically if it does not already exist."""
    from app.auth import hash_password
    from app.models import User, LearnerProfile
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "admin@navgurukul.org"))
        admin = result.scalar_one_or_none()
        if not admin:
            admin = User(
                email="admin@navgurukul.org",
                hashed_password=hash_password("navgurukul"),
                role="admin",
                status="active"
            )
            session.add(admin)
            await session.flush()
            session.add(LearnerProfile(user_id=admin.id))
            await session.commit()
            import logging
            logging.info("Default admin user seeded successfully.")
        else:
            import logging
            logging.info("Default admin user already exists. Skipping seeding.")

