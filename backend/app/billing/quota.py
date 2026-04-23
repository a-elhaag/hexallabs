from __future__ import annotations

from datetime import date, datetime, timedelta, timezone as tz
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing import config
from app.db.models.user_quota import UserQuota


class QuotaService:

    @staticmethod
    def available(quota: UserQuota) -> int:
        cap = int(config.DAILY_BASE_TOKENS * config.HARD_CAP_MULTIPLIER)
        return min(config.DAILY_BASE_TOKENS + quota.rollover_balance, cap)

    @staticmethod
    def check(quota: UserQuota) -> None:
        if quota.daily_used >= QuotaService.available(quota):
            tomorrow = datetime.now(tz.utc).date() + timedelta(days=1)
            resets_at = datetime.combine(tomorrow, datetime.min.time()).replace(tzinfo=tz.utc)
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
        quota = await db.get(UserQuota, user_id)
        today: date = datetime.now(tz.utc).date()

        if quota is None:
            quota = UserQuota(
                user_id=user_id,
                daily_used=0,
                rollover_balance=0,
                window_start_date=today,
                timezone=user_tz,
            )
            db.add(quota)
            await db.flush()
            return quota

        # Lazy daily reset — trigger when last update was on a prior calendar day
        updated_date: date = (
            quota.updated_at.date()
            if quota.updated_at.tzinfo is None
            else quota.updated_at.astimezone(tz.utc).date()
        )
        if updated_date < today:
            avail = QuotaService.available(quota)
            leftover = max(avail - quota.daily_used, 0)
            new_rollover = int(leftover * config.ROLLOVER_RATE)

            days_in_window = (today - quota.window_start_date).days
            if days_in_window >= config.ROLLOVER_WINDOW_DAYS:
                new_rollover = 0
                quota.window_start_date = today

            quota.daily_used = 0
            quota.rollover_balance = new_rollover
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
        avail_before = QuotaService.available(quota)
        quota.daily_used += weighted
        leftover = max(avail_before - quota.daily_used, 0)
        quota.rollover_balance = int(leftover * config.ROLLOVER_RATE)
        await db.flush()
