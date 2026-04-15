"""
Quick DB connection test — run before starting the server.
Uses psycopg2 (sync) so you get a clear error if the connection fails.

Usage:
    cd backend
    python test_db.py
"""

import os
import sys

import psycopg2
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

HOST = "hexallabs-db.postgres.database.azure.com"
PORT = 5432
USER = "Hexallabs"
DB = "postgres"


def main():
    password = os.getenv("DB_PASSWORD") or os.getenv("PGPASSWORD")

    if not password:
        # Try to extract from DATABASE_URL
        db_url = os.getenv("DATABASE_URL", "")
        if "@" in db_url and ":" in db_url:
            try:
                # postgresql+asyncpg://user:password@host/db
                creds = db_url.split("://")[1].split("@")[0]
                password = creds.split(":")[1]
            except (IndexError, ValueError):
                pass

    if not password:
        print("ERROR: No password found.")
        print("Set DB_PASSWORD in backend/.env or pass it as an env var.")
        sys.exit(1)

    print(f"Connecting to {HOST}:{PORT} as {USER}...")

    try:
        cnx = psycopg2.connect(
            user=USER,
            password=password,
            host=HOST,
            port=PORT,
            database=DB,
            sslmode="require",
        )
        cursor = cnx.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"Connected! PostgreSQL version:\n  {version}")
        cursor.close()
        cnx.close()
    except psycopg2.OperationalError as e:
        print(f"Connection FAILED:\n  {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
