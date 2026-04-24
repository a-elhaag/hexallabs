from __future__ import annotations

from datetime import datetime, timedelta, timezone as tz

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthUser, get_current_user
from app.billing.quota import QuotaService, _WINDOW
from app.db import get_session
from app.db.models.user_quota import UserQuota

router = APIRouter(prefix="/api", tags=["quota"])


class QuotaStatus(BaseModel):
    percentage_used: float  # 0.0–100.0
    window_started: bool
    window_start: datetime | None
    resets_at: datetime | None


@router.get("/quota", response_model=QuotaStatus)
async def get_quota(
    user: AuthUser = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_session),  # noqa: B008
) -> QuotaStatus:
    """Return quota state without creating or mutating any row.

    If user has never made an LLM request, returns used=0, window_started=False.
    The 24h window only starts on the first actual LLM request.
    """
    quota: UserQuota | None = await db.get(UserQuota, user.id)

    if quota is None:
        return QuotaStatus(
            percentage_used=0.0,
            window_started=False,
            window_start=None,
            resets_at=None,
        )

    available = QuotaService.available(quota)
    pct = round(min(quota.daily_used / available * 100, 100.0), 2) if available else 100.0
    window_start = QuotaService._window_start_utc(quota)
    resets_at = window_start + _WINDOW

    return QuotaStatus(
        percentage_used=pct,
        window_started=True,
        window_start=window_start,
        resets_at=resets_at,
    )
