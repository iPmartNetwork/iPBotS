"""Database engine and session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bot.config import settings

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.APP_DEBUG,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_db_engine():
    """Create database engine."""
    return engine


async def create_tables():
    """Create all database tables."""
    from core.database.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop all database tables."""
    from core.database.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session context manager."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
