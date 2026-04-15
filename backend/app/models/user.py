"""
Prisma-managed table — NextAuth owns creation/writes to `users`.
This stub registers the table in SQLAlchemy metadata for FK validation only.
"""
from __future__ import annotations

from sqlalchemy import Column, String, Table

from app.database import Base

# Thin reference — create_all will skip this if Prisma already created it
users_table = Table(
    "users",
    Base.metadata,
    Column("id", String, primary_key=True),
    extend_existing=True,
)
