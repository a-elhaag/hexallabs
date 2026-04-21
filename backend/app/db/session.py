from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings, get_settings


@lru_cache(maxsize=1)
def _build_engine(url: str, pool_size: int, max_overflow: int) -> AsyncEngine:
    return create_async_engine(
        url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
        future=True,
    )


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    s = settings or get_settings()
    return _build_engine(s.database_url, s.database_pool_size, s.database_max_overflow)


@lru_cache(maxsize=1)
def _build_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


def get_sessionmaker(
    settings: Settings | None = None,
) -> async_sessionmaker[AsyncSession]:
    return _build_sessionmaker(get_engine(settings))


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency. Yields a session, rolls back on exception, always closes."""
    sm = get_sessionmaker()
    async with sm() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()


async def dispose_engine() -> None:
    engine = get_engine()
    await engine.dispose()
    _build_engine.cache_clear()
    _build_sessionmaker.cache_clear()
