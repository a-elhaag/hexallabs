import { NextResponse } from "next/server";
import { db } from "~/server/db";

// POST /api/register — email/password sign-up
// Triggers the createUser event in auth config which provisions Core subscription
export async function POST(req: Request) {
  const body = (await req.json()) as { name?: string; email?: string; password?: string };

  if (!body.email || !body.password) {
    return NextResponse.json({ error: "email and password required" }, { status: 400 });
  }

  const existing = await db.user.findUnique({ where: { email: body.email } });
  if (existing) {
    return NextResponse.json({ error: "Email already in use" }, { status: 409 });
  }

  const { hash } = await import("bcryptjs");
  const hashed = await hash(body.password, 12);

  const user = await db.user.create({
    data: {
      name: body.name ?? null,
      email: body.email,
      password: hashed,
    },
  });

  // Manually trigger subscription provisioning (createUser event only fires via adapter)
  const core = await db.pricingTier.findUnique({ where: { name: "core" } });
  if (core) {
    const { addWeeks, startOfWeek } = await import("date-fns");
    const now = new Date();
    const nextWeek = addWeeks(startOfWeek(now, { weekStartsOn: 1 }), 1);

    await db.subscription.create({
      data: {
        userId: user.id,
        tierId: core.id,
        currentMonthBudgetUsd: core.monthlyUsageUsd,
        currentWeekBudgetUsd: core.weeklyUsageUsd,
        weekResetDate: nextWeek,
        status: "active",
      },
    });
  }

  return NextResponse.json({ id: user.id, email: user.email }, { status: 201 });
}
