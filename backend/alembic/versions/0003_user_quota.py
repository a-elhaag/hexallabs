"""add user_quota table

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-23
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_quota",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("daily_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rollover_balance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("window_start_date", sa.Date(), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="UTC"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("user_quota")
