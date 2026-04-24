"""Test cloud Supabase DB connection + list public schema tables.

Reads DATABASE_URL from backend/.env via python-dotenv. No app imports — pure asyncpg.

Usage:
    cd backend && uv run python scripts/test_db.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import asyncpg
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _normalize(url: str) -> str:
    """asyncpg wants plain postgresql://, strip SQLAlchemy's '+asyncpg' suffix."""
    parsed = urlparse(url)
    scheme = parsed.scheme.replace("+asyncpg", "").replace("postgresql", "postgres")
    return urlunparse(parsed._replace(scheme=scheme))


async def main() -> int:
    raw = os.getenv("DATABASE_URL")
    if not raw:
        print("ERROR: DATABASE_URL not set in backend/.env", file=sys.stderr)
        return 1

    url = _normalize(raw)
    host = urlparse(url).hostname
    print(f"Connecting to {host} ...")

    try:
        conn = await asyncpg.connect(url, ssl="require", timeout=10)
    except Exception as e:
        print(f"FAIL: connection error: {e}", file=sys.stderr)
        return 2

    try:
        version = await conn.fetchval("SELECT version();")
        print(f"OK — {version.split(',')[0]}")

        rows = await conn.fetch(
            """
            SELECT schemaname, tablename
            FROM pg_tables
            WHERE schemaname IN ('public', 'auth')
            ORDER BY schemaname, tablename;
            """
        )
        if not rows:
            print("(no tables in public/auth schema)")
            return 0

        by_schema: dict[str, list[str]] = {}
        for r in rows:
            by_schema.setdefault(r["schemaname"], []).append(r["tablename"])

        for schema, tables in by_schema.items():
            print(f"\n{schema} ({len(tables)} tables):")
            for t in tables:
                print(f"  - {t}")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
