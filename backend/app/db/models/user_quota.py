from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models._common import updated_at_col


class UserQuota(Base):
    __tablename__ = "user_quota"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    daily_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rollover_balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    window_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    updated_at: Mapped[datetime] = updated_at_col()
