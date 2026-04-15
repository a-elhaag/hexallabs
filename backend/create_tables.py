"""
Create backend-owned SQLAlchemy tables (council_configs, executions).

Run AFTER `pnpm db:push` in frontend — Prisma creates `users` first,
then SQLAlchemy creates the FK-dependent tables.

Usage:
    cd backend
    python create_tables.py
"""

import asyncio

from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

from app.database import engine, Base  # noqa: E402 — env must load first
import app.models  # noqa: F401 — registers all models in metadata


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
    print("Tables created (or already exist):")
    async with engine.begin() as conn:
        result = await conn.run_sync(
            lambda c: c.execute(
                __import__("sqlalchemy").text(
                    "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
                )
            ).fetchall()
        )
        for row in result:
            print(f"  {row[0]}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
