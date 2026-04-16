import { NextResponse } from "next/server";
import { db } from "~/server/db";
import { getSessionUser } from "~/server/auth/session";

// GET /api/council — list user's councils with execution count
export async function GET() {
  const user = await getSessionUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const councils = await db.councilConfig.findMany({
    where: { userId: user.id },
    orderBy: { createdAt: "desc" },
    include: {
      _count: { select: { executions: true } },
    },
  });

  return NextResponse.json(councils);
}

// POST /api/council — create a new council config
export async function POST(req: Request) {
  const user = await getSessionUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const body = (await req.json()) as {
    name?: string;
    models?: string[];
    systemPrompt?: string;
    organizerModel?: string | null;
  };

  if (!body.name || !body.models?.length || !body.systemPrompt) {
    return NextResponse.json({ error: "name, models, systemPrompt required" }, { status: 400 });
  }

  // Enforce tier max models
  const sub = await db.subscription.findUnique({
    where: { userId: user.id },
    include: { tier: true },
  });
  const maxModels = sub?.tier.maxModels ?? 2;
  if (body.models.length > maxModels) {
    return NextResponse.json(
      { error: `Your plan allows up to ${maxModels} models` },
      { status: 403 },
    );
  }

  const council = await db.councilConfig.create({
    data: {
      userId: user.id,
      name: body.name,
      models: body.models,
      systemPrompt: body.systemPrompt,
      organizerModel: body.organizerModel ?? "gpt-5.4-mini",
    },
  });

  return NextResponse.json(council, { status: 201 });
}
