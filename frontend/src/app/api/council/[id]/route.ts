import { NextResponse } from "next/server";
import { db } from "~/server/db";
import { getSessionUser } from "~/server/auth/session";

// GET /api/council/[id] — get a single council with recent executions
export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const user = await getSessionUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { id } = await params;

  const council = await db.councilConfig.findFirst({
    where: { id, userId: user.id },
    include: {
      executions: {
        orderBy: { createdAt: "desc" },
        take: 20,
        select: {
          id: true,
          query: true,
          status: true,
          synthesis: true,
          costBreakdown: true,
          createdAt: true,
        },
      },
    },
  });

  if (!council) return NextResponse.json({ error: "Not found" }, { status: 404 });

  return NextResponse.json(council);
}

// DELETE /api/council/[id] — delete a council (cascades executions)
export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const user = await getSessionUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { id } = await params;

  const council = await db.councilConfig.findFirst({
    where: { id, userId: user.id },
  });
  if (!council) return NextResponse.json({ error: "Not found" }, { status: 404 });

  await db.councilConfig.delete({ where: { id } });

  return new NextResponse(null, { status: 204 });
}
