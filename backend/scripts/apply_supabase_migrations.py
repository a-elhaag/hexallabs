"""Apply supabase/migrations/*.sql files directly via asyncpg.

Use this instead of `supabase db push` when the Supabase CLI isn't installed.
Runs every file in lexical order, so prefix filenames with UTC timestamps.

Safe to re-run: all SQL in supabase/migrations/ uses IF NOT EXISTS / OR REPLACE.

Usage:
    uv run python scripts/apply_supabase_migrations.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = REPO_ROOT / "supabase" / "migrations"


async def main() -> int:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")  # noqa: ASYNC240
    raw = os.environ.get("DATABASE_URL")
    if not raw:
        print("error: DATABASE_URL not set", file=sys.stderr)
        return 1

    # asyncpg wants plain postgresql://, not SQLAlchemy's postgresql+asyncpg://
    url = raw.replace("postgresql+asyncpg://", "postgresql://", 1)

    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not files:
        print(f"no migrations found in {MIGRATIONS_DIR}")
        return 0

    conn = await asyncpg.connect(url, statement_cache_size=0)
    try:
        for f in files:
            print(f"applying {f.name} ... ", end="", flush=True)
            await conn.execute(f.read_text())
            print("ok")
    finally:
        await conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
