"""
APScheduler — background jobs.

Jobs:
  - weekly_budget_reset: every Monday 00:00 UTC
    Rolls over 50% of unused weekly budget, resets usedThisWeekUsd.
"""
from __future__ import annotations

import uuid
import json
import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text

from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")


def _next_monday_utc() -> datetime:
    now = datetime.now(timezone.utc)
    days_until_monday = (7 - now.weekday()) % 7 or 7  # always next Monday
    return (now + timedelta(days=days_until_monday)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


async def weekly_budget_reset() -> None:
    """
    Run every Monday 00:00 UTC.
    For each active subscription:
      - rollover = min(unused_weekly_usd, weeklyUsageUsd * rolloverPct)
      - new_budget = weeklyUsageUsd + rollover
      - Reset usedThisWeekUsd = 0
      - Update currentWeekBudgetUsd = new_budget
      - Update rolloverBalanceUsd = rollover
      - Update weekResetDate = next Monday
    """
    logger.info("Running weekly budget reset...")
    next_reset = _next_monday_utc()

    async with AsyncSessionLocal() as db:
        # Fetch all active subscriptions with tier info
        rows = await db.execute(
            text("""
                SELECT
                    s.id,
                    s."userId",
                    s."currentWeekBudgetUsd",
                    s."usedThisWeekUsd",
                    pt."weeklyUsageUsd",
                    pt."rolloverPct"
                FROM subscriptions s
                JOIN pricing_tiers pt ON s."tierId" = pt.id
                WHERE s.status = 'active'
            """)
        )
        subs = rows.mappings().all()
        logger.info(f"  Resetting {len(subs)} subscriptions")

        for sub in subs:
            unused = max(0.0, sub["currentWeekBudgetUsd"] - sub["usedThisWeekUsd"])
            rollover = round(min(unused, sub["weeklyUsageUsd"] * sub["rolloverPct"]), 6)
            new_budget = round(sub["weeklyUsageUsd"] + rollover, 6)

            await db.execute(
                text("""
                    UPDATE subscriptions
                    SET
                        "currentWeekBudgetUsd" = :new_budget,
                        "usedThisWeekUsd"       = 0,
                        "rolloverBalanceUsd"    = :rollover,
                        "weekResetDate"         = :next_reset,
                        "updatedAt"             = NOW()
                    WHERE id = :sub_id
                """),
                {
                    "new_budget": new_budget,
                    "rollover": rollover,
                    "next_reset": next_reset,
                    "sub_id": sub["id"],
                },
            )

            # BillingEvent audit row
            await db.execute(
                text("""
                    INSERT INTO billing_events (id, "userId", "eventType", "amountUsd", metadata, "createdAt")
                    VALUES (:id, :user_id, 'weekly_reset', 0, :metadata::jsonb, NOW())
                """),
                {
                    "id": str(uuid.uuid4()),
                    "user_id": sub["userId"],
                    "metadata": json.dumps({
                        "rollover_usd": rollover,
                        "new_budget_usd": new_budget,
                        "reset_date": next_reset.isoformat(),
                    }),
                },
            )

        await db.commit()
    logger.info("Weekly budget reset complete.")


def setup_scheduler() -> AsyncIOScheduler:
    """Register all jobs and return the scheduler (not yet started)."""
    scheduler.add_job(
        weekly_budget_reset,
        CronTrigger(day_of_week="mon", hour=0, minute=0, timezone="UTC"),
        id="weekly_budget_reset",
        replace_existing=True,
    )
    return scheduler
