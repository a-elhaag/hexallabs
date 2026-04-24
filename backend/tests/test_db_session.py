from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.db import get_engine, get_sessionmaker
from app.db.session import _build_engine, _build_sessionmaker


def test_get_engine_is_async_engine() -> None:
    _build_engine.cache_clear()
    _build_sessionmaker.cache_clear()
    engine = get_engine()
    assert isinstance(engine, AsyncEngine)


async def test_sessionmaker_produces_async_sessions() -> None:
    _build_engine.cache_clear()
    _build_sessionmaker.cache_clear()
    sm = get_sessionmaker()
    assert isinstance(sm, async_sessionmaker)
    async with sm() as session:
        assert isinstance(session, AsyncSession)


def test_engine_is_cached() -> None:
    _build_engine.cache_clear()
    _build_sessionmaker.cache_clear()
    a = get_engine()
    b = get_engine()
    assert a is b
