import { NextResponse } from "next/server";
import { db } from "~/server/db";
import { getSessionUser } from "~/server/auth/session";

// GET /api/subscription — current subscription, tier info, usage meters
export async function GET() {
  const user = await getSessionUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const sub = await db.subscription.findUnique({
    where: { userId: user.id },
    include: { tier: true },
  });

  if (!sub) return NextResponse.json({ subscription: null });

  return NextResponse.json({
    subscription: {
      id: sub.id,
      status: sub.status,
      tier: {
        name: sub.tier.name,
        displayName: sub.tier.displayName,
        monthlyPriceUsd: sub.tier.monthlyPriceUsd,
        monthlyUsageUsd: sub.tier.monthlyUsageUsd,
        weeklyUsageUsd: sub.tier.weeklyUsageUsd,
        maxModels: sub.tier.maxModels,
      },
      usage: {
        usedThisWeekUsd: sub.usedThisWeekUsd,
        currentWeekBudgetUsd: sub.currentWeekBudgetUsd,
        usedThisMonthUsd: sub.usedThisMonthUsd,
        currentMonthBudgetUsd: sub.currentMonthBudgetUsd,
        rolloverBalanceUsd: sub.rolloverBalanceUsd,
        weekResetDate: sub.weekResetDate,
      },
    },
  });
}
