import { NextResponse } from "next/server";
import { db } from "~/server/db";
import { getSessionUser } from "~/server/auth/session";

const MODELS = [
  { id: "gpt-5.1-chat",           whiteLabelName: "Apex",    role: "Chairman / default",  tier: "core" },
  { id: "gpt-5.4-mini",           whiteLabelName: "Swift",   role: "Organizer (fast)",    tier: "core" },
  { id: "o4-mini",                whiteLabelName: "Prism",   role: "Reasoning",           tier: "elite" },
  { id: "DeepSeek-V3.2-Speciale", whiteLabelName: "Depth",   role: "Deep analysis",       tier: "elite" },
  { id: "Llama-3.3-70B-Instruct", whiteLabelName: "Atlas",   role: "Open-source",         tier: "elite" },
  { id: "Kimi-K2.5",              whiteLabelName: "Horizon", role: "Long context",        tier: "elite" },
  { id: "grok-4-20-reasoning",    whiteLabelName: "Pulse",   role: "Latest reasoning",    tier: "elite" },
] as const;

// GET /api/models — models catalog, filtered by user's tier
export async function GET() {
  const user = await getSessionUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const sub = await db.subscription.findUnique({
    where: { userId: user.id },
    include: { tier: true },
  });

  const tierName = sub?.tier.name ?? "core";
  const maxModels = sub?.tier.maxModels ?? 2;

  // Core can only use core-tier models (Apex + Swift)
  const available = tierName === "core"
    ? MODELS.filter((m) => m.tier === "core")
    : MODELS;

  return NextResponse.json({ models: available, maxModels, tier: tierName });
}
