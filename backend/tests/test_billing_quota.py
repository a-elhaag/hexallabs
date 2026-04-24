"""Tests for app.billing.quota.QuotaService.

Uses the FakeSession pattern from conftest.py.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone as tz, timedelta
from typing import Any

import pytest

from app.billing.quota import QuotaService
from app.billing import config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeQuota:
    """Plain-Python stand-in for UserQuota that avoids SQLAlchemy instrumentation."""

    def __init__(
        self,
        user_id: uuid.UUID | None = None,
        daily_used: int = 0,
        rollover_balance: int = 0,
        window_start: datetime | None = None,
        timezone: str = "UTC",
        updated_at: datetime | None = None,
    ) -> None:
        self.user_id = user_id or uuid.uuid4()
        self.daily_used = daily_used
        self.rollover_balance = rollover_balance
        self.window_start = window_start or datetime.now(tz.utc)
        self.timezone = timezone
        self.updated_at = updated_at or datetime.now(tz.utc)


def _make_quota(
    user_id: uuid.UUID | None = None,
    daily_used: int = 0,
    rollover_balance: int = 0,
    window_start: datetime | None = None,
    timezone: str = "UTC",
    updated_at: datetime | None = None,
) -> _FakeQuota:
    """Construct a _FakeQuota with controlled field values."""
    return _FakeQuota(
        user_id=user_id,
        daily_used=daily_used,
        rollover_balance=rollover_balance,
        window_start=window_start,
        timezone=timezone,
        updated_at=updated_at,
    )


class FakeSession:
    """Minimal AsyncSession stand-in that supports get() override for tests."""

    def __init__(self, existing: object | None = None) -> None:
        self.added: list[object] = []
        self._existing = existing

    def add(self, obj: object) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def get(self, _model: Any, _id: Any) -> object | None:
        return self._existing


# ---------------------------------------------------------------------------
# Tests: get_or_create
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_or_create_fresh_user() -> None:
    """A new user gets a fresh UserQuota row created and flushed."""
    db = FakeSession(existing=None)
    user_id = uuid.uuid4()

    quota = await QuotaService.get_or_create(db, user_id)

    assert quota.user_id == user_id
    assert quota.daily_used == 0
    assert quota.rollover_balance == 0
    assert quota.window_start.date() == datetime.now(tz.utc).date()
    assert db.added == [quota]


@pytest.mark.asyncio
async def test_get_or_create_existing_same_day() -> None:
    """Existing user with same-day updated_at is returned without modification."""
    today = datetime.now(tz.utc)
    existing = _make_quota(daily_used=10, rollover_balance=5, window_start=today)
    db = FakeSession(existing=existing)

    quota = await QuotaService.get_or_create(db, existing.user_id)

    assert quota is existing
    assert quota.daily_used == 10  # unchanged
    assert quota.rollover_balance == 5  # unchanged


@pytest.mark.asyncio
async def test_get_or_create_new_day_resets_and_computes_rollover() -> None:
    """Day transition: daily_used resets, rollover computed from leftover."""
    yesterday = datetime.now(tz.utc) - timedelta(days=1)
    # daily_used=30 out of available=100 (base=100, rollover=0)
    existing = _make_quota(
        daily_used=30,
        rollover_balance=0,
        window_start=datetime.now(tz.utc) - timedelta(days=2),  # 2 days ago, within window
        updated_at=yesterday,
    )
    db = FakeSession(existing=existing)

    quota = await QuotaService.get_or_create(db, existing.user_id)

    # leftover = 100 - 30 = 70, rollover = int(70 * 0.5) = 35
    assert quota.daily_used == 0
    assert quota.rollover_balance == 35


@pytest.mark.asyncio
async def test_get_or_create_day4_zeroes_rollover_and_resets_window() -> None:
    """Day 4 of window (>= ROLLOVER_WINDOW_DAYS=3): rollover zeroed, window reset."""
    four_days_ago = datetime.now(tz.utc) - timedelta(days=4)
    existing = _make_quota(
        daily_used=10,
        rollover_balance=20,
        window_start=four_days_ago,
        updated_at=four_days_ago,
    )
    db = FakeSession(existing=existing)

    quota = await QuotaService.get_or_create(db, existing.user_id)

    assert quota.rollover_balance == 0
    assert quota.window_start.date() == datetime.now(tz.utc).date()
    assert quota.daily_used == 0


# ---------------------------------------------------------------------------
# Tests: available
# ---------------------------------------------------------------------------

def test_available_base_plus_rollover_below_cap() -> None:
    """available = base + rollover when that sum is below hard cap."""
    quota = _make_quota(rollover_balance=10)
    # base=100, rollover=10 → 110; cap = int(100 * 1.5) = 150
    assert QuotaService.available(quota) == 110


def test_available_capped_at_hard_cap() -> None:
    """available is capped at HARD_CAP_MULTIPLIER * DAILY_BASE_TOKENS."""
    quota = _make_quota(rollover_balance=200)  # would be 300 without cap
    cap = int(config.DAILY_BASE_TOKENS * config.HARD_CAP_MULTIPLIER)  # 150
    assert QuotaService.available(quota) == cap


# ---------------------------------------------------------------------------
# Tests: check
# ---------------------------------------------------------------------------

def test_check_passes_when_under_quota() -> None:
    """No exception raised when daily_used < available."""
    quota = _make_quota(daily_used=0, rollover_balance=0)
    # available = 100; used = 0
    QuotaService.check(quota)  # should not raise


def test_check_raises_429_when_at_quota() -> None:
    """HTTP 429 raised when daily_used >= available."""
    from fastapi import HTTPException
    quota = _make_quota(daily_used=100, rollover_balance=0)
    # available = 100; used = 100 → exceeded
    with pytest.raises(HTTPException) as exc_info:
        QuotaService.check(quota)

    assert exc_info.value.status_code == 429
    detail = exc_info.value.detail
    assert isinstance(detail, dict)
    assert detail["detail"] == "daily quota exceeded"
    assert "resets_at" in detail
    assert detail["available"] == 100


def test_check_raises_429_when_over_quota() -> None:
    """HTTP 429 raised when daily_used > available (overshoot)."""
    from fastapi import HTTPException
    quota = _make_quota(daily_used=120, rollover_balance=0)
    with pytest.raises(HTTPException) as exc_info:
        QuotaService.check(quota)
    assert exc_info.value.status_code == 429


# ---------------------------------------------------------------------------
# Tests: deduct
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_deduct_weighted_tokens_apex() -> None:
    """Deduct with Apex (weight=2.0) doubles the token cost."""
    db = FakeSession()
    quota = _make_quota(daily_used=0, rollover_balance=0)

    await QuotaService.deduct(db, quota, tokens_out=10, model="Apex")

    # weighted = int(10 * 2.0) = 20
    assert quota.daily_used == 20


@pytest.mark.asyncio
async def test_deduct_multiple_same_day_accumulate() -> None:
    """Multiple deducts on the same day accumulate in daily_used."""
    db = FakeSession()
    quota = _make_quota(daily_used=0, rollover_balance=0)

    await QuotaService.deduct(db, quota, tokens_out=10, model="Swift")  # weight=1.0 → 10
    await QuotaService.deduct(db, quota, tokens_out=10, model="Swift")  # weight=1.0 → 10

    assert quota.daily_used == 20


@pytest.mark.asyncio
async def test_deduct_unknown_model_uses_default_weight() -> None:
    """Unknown model falls back to weight=1.0."""
    db = FakeSession()
    quota = _make_quota(daily_used=0, rollover_balance=0)

    await QuotaService.deduct(db, quota, tokens_out=15, model="UnknownModel")

    assert quota.daily_used == 15  # int(15 * 1.0) = 15


@pytest.mark.asyncio
async def test_deduct_only_updates_daily_used() -> None:
    """deduct() updates daily_used only — rollover is computed at window reset, not here."""
    db = FakeSession()
    quota = _make_quota(daily_used=0, rollover_balance=5)

    await QuotaService.deduct(db, quota, tokens_out=60, model="Swift")  # weight=1.0

    assert quota.daily_used == 60
    assert quota.rollover_balance == 5  # unchanged by design
