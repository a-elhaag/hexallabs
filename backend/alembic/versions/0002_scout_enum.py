"""Widen sessions.scout_enabled from boolean to varchar(8) for scout mode enum.

Revision ID: 0002
Revises: 0001
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Cast boolean to varchar, mapping true→"auto", false→"off".
    op.alter_column(
        "sessions",
        "scout_enabled",
        existing_type=sa.Boolean(),
        type_=sa.String(8),
        postgresql_using="CASE WHEN scout_enabled THEN 'auto' ELSE 'off' END",
        nullable=False,
        server_default="off",
    )


def downgrade() -> None:
    op.alter_column(
        "sessions",
        "scout_enabled",
        existing_type=sa.String(8),
        type_=sa.Boolean(),
        postgresql_using="CASE WHEN scout_enabled = 'off' THEN false ELSE true END",
        nullable=False,
        server_default=sa.false(),
    )
