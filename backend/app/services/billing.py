"""
Billing service — budget enforcement, usage logging, deductions.

All tables (subscriptions, usage_logs, billing_events, pricing_tiers) are
Prisma-managed, so we access them via raw SQL through the SQLAlchemy session.
Prisma uses camelCase column names in PostgreSQL (no @map on fields).
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.council import COST_PER_1K


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------


async def get_subscription(db: AsyncSession, user_id: str) -> dict[str, Any] | None:
    """Fetch user's active subscription joined with tier limits."""
    result = await db.execute(
        text("""
            SELECT
                s.id,
                s."userId",
                s."tierId",
                s."currentMonthBudgetUsd",
                s."usedThisMonthUsd",
                s."rolloverBalanceUsd",
                s."currentWeekBudgetUsd",
                s."usedThisWeekUsd",
                s."weekResetDate",
                s.status,
                pt."weeklyUsageUsd",
                pt."monthlyUsageUsd",
                pt."maxModels",
                pt."rolloverPct"
            FROM subscriptions s
            JOIN pricing_tiers pt ON s."tierId" = pt.id
            WHERE s."userId" = :user_id AND s.status = 'active'
        """),
        {"user_id": user_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Enforcement
# ---------------------------------------------------------------------------


async def check_budget(
    db: AsyncSession, user_id: str
) -> tuple[bool, str]:
    """
    Returns (can_proceed, error_message).
    No subscription → allowed with Core tier defaults (no hard budget block).
    """
    sub = await get_subscription(db, user_id)
    if not sub:
        return True, ""  # no sub = no enforcement for now; frontend handles signup

    weekly_remaining = sub["currentWeekBudgetUsd"] - sub["usedThisWeekUsd"]
    if weekly_remaining <= 0:
        return False, "Weekly budget exhausted. Resets next Monday."

    monthly_remaining = sub["currentMonthBudgetUsd"] - sub["usedThisMonthUsd"]
    if monthly_remaining <= 0:
        return False, "Monthly budget exhausted."

    return True, ""


async def check_max_models(
    db: AsyncSession, user_id: str, model_count: int
) -> tuple[bool, str]:
    """Returns (can_proceed, error_message). No subscription → Core limit of 2."""
    sub = await get_subscription(db, user_id)
    max_models = sub["maxModels"] if sub else 2  # Core default

    if model_count > max_models:
        tier = "your tier" if sub else "the free Core tier"
        return False, f"{model_count} models requested but {tier} allows {max_models} max."

    return True, ""


# ---------------------------------------------------------------------------
# Usage logging + deduction
# ---------------------------------------------------------------------------


async def log_and_deduct(
    db: AsyncSession,
    user_id: str,
    execution_id: str,
    model_usage: dict[str, dict],   # model_name → {input_tokens, output_tokens, total_tokens}
    cost_breakdown: dict[str, float],  # model_name → billed_usd
) -> None:
    """
    1. Insert a UsageLog row per model.
    2. Deduct total cost from subscription (week + month).
    3. Insert a BillingEvent for the deduction.
    Silently skips if user has no subscription (no budget to deduct).
    """
    total_billed = sum(cost_breakdown.values())
    if total_billed <= 0:
        return

    # 1. Usage log rows per model
    for model_name, usage in model_usage.items():
        billed = cost_breakdown.get(model_name, 0.0)
        if billed <= 0:
            continue
        await db.execute(
            text("""
                INSERT INTO usage_logs (
                    id, "userId", "executionId", "modelName", "deploymentName",
                    "inputTokens", "outputTokens", "totalTokens",
                    "ratePerK", "billedUsd", "createdAt"
                ) VALUES (
                    :id, :user_id, :execution_id, :model_name, :deployment_name,
                    :input_tokens, :output_tokens, :total_tokens,
                    :rate_per_k, :billed_usd, NOW()
                )
            """),
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "execution_id": execution_id,
                "model_name": model_name,
                "deployment_name": model_name,  # deployment name == key in our setup
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "rate_per_k": COST_PER_1K.get(model_name, 0.0),
                "billed_usd": billed,
            },
        )

    # 2. Deduct from subscription
    updated = await db.execute(
        text("""
            UPDATE subscriptions
            SET
                "usedThisWeekUsd"  = "usedThisWeekUsd"  + :amount,
                "usedThisMonthUsd" = "usedThisMonthUsd" + :amount,
                "updatedAt"        = NOW()
            WHERE "userId" = :user_id
            RETURNING id
        """),
        {"amount": total_billed, "user_id": user_id},
    )
    if not updated.first():
        # No subscription — skip billing event
        await db.commit()
        return

    # 3. BillingEvent audit row
    await db.execute(
        text("""
            INSERT INTO billing_events (id, "userId", "eventType", "amountUsd", metadata, "createdAt")
            VALUES (:id, :user_id, 'usage_deduction', :amount, :metadata::jsonb, NOW())
        """),
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "amount": total_billed,
            "metadata": __import__("json").dumps({"execution_id": execution_id}),
        },
    )

    await db.commit()
