"""replace user_quota.window_start_date with window_start timestamp

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-23
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new timestamptz column, backfill from window_start_date, then drop old.
    op.add_column(
        "user_quota",
        sa.Column(
            "window_start",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.execute(
        "UPDATE user_quota SET window_start = window_start_date::timestamptz"
    )
    op.alter_column("user_quota", "window_start", nullable=False)
    op.drop_column("user_quota", "window_start_date")


def downgrade() -> None:
    op.add_column(
        "user_quota",
        sa.Column("window_start_date", sa.Date(), nullable=True),
    )
    op.execute(
        "UPDATE user_quota SET window_start_date = window_start::date"
    )
    op.alter_column("user_quota", "window_start_date", nullable=False)
    op.drop_column("user_quota", "window_start")
