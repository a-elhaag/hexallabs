from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Execution(Base):
    __tablename__ = "executions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    council_id: Mapped[str] = mapped_column(
        String, ForeignKey("council_configs.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    # "pending" | "running" | "complete" | "error"
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")

    model_responses: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    peer_reviews: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    synthesis: Mapped[str | None] = mapped_column(Text)
    cost_breakdown: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    council: Mapped[CouncilConfig] = relationship(
        "CouncilConfig", back_populates="executions"
    )
    user: Mapped[User] = relationship("User", back_populates="executions")


from app.models.council import CouncilConfig  # noqa: E402
from app.models.user import User  # noqa: E402
