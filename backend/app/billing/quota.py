from __future__ import annotations

from datetime import datetime, timedelta, timezone as tz
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing import config
from app.db.models.user_quota import UserQuota

_WINDOW = timedelta(hours=24)


class QuotaService:

    @staticmethod
    def available(quota: UserQuota) -> int:
        cap = int(config.DAILY_BASE_TOKENS * config.HARD_CAP_MULTIPLIER)
        return min(config.DAILY_BASE_TOKENS + quota.rollover_balance, cap)

    @staticmethod
    def _window_start_utc(quota: UserQuota) -> datetime:
        ws = quota.window_start
        if ws.tzinfo is None:
            return ws.replace(tzinfo=tz.utc)
        return ws.astimezone(tz.utc)

    @staticmethod
    def check(quota: UserQuota) -> None:
        if quota.daily_used >= QuotaService.available(quota):
            resets_at = QuotaService._window_start_utc(quota) + _WINDOW
            raise HTTPException(
                status_code=429,
                detail={
                    "detail": "daily quota exceeded",
                    "available": QuotaService.available(quota),
                    "resets_at": resets_at.isoformat(),
                },
            )

    @staticmethod
    async def get_or_create(
        db: AsyncSession,
        user_id: UUID,
        user_tz: str = "UTC",
    ) -> UserQuota:
        now = datetime.now(tz.utc)
        quota = await db.get(UserQuota, user_id)

        if quota is None:
            # First ever request — window opens now.
            quota = UserQuota(
                user_id=user_id,
                daily_used=0,
                rollover_balance=0,
                window_start=now,
                timezone=user_tz,
            )
            db.add(quota)
            await db.flush()
            return quota

        window_start = QuotaService._window_start_utc(quota)
        if now - window_start >= _WINDOW:
            # 24h elapsed since last window open. Reset on this request.
            # New window starts NOW (user activity), not at the theoretical boundary.
            avail = QuotaService.available(quota)
            leftover = max(avail - quota.daily_used, 0)
            new_rollover = int(leftover * config.ROLLOVER_RATE)

            elapsed_windows = int((now - window_start) / _WINDOW)
            if elapsed_windows >= config.ROLLOVER_WINDOW_DAYS:
                new_rollover = 0

            quota.daily_used = 0
            quota.rollover_balance = new_rollover
            quota.window_start = now
            await db.flush()

        return quota

    @staticmethod
    async def deduct(
        db: AsyncSession,
        quota: UserQuota,
        tokens_out: int,
        model: str,
    ) -> None:
        weight = config.MODEL_WEIGHTS.get(model, 1.0)
        weighted = int(tokens_out * weight)
        quota.daily_used += weighted
        # rollover_balance intentionally NOT touched here — computed once at
        # window reset in get_or_create() only.
        await db.flush()
