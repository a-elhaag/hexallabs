from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CouncilConfig(Base):
    __tablename__ = "council_configs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    models: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    organizer_model: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    executions: Mapped[list[Execution]] = relationship(
        "Execution", back_populates="council", cascade="all, delete-orphan"
    )


from app.models.execution import Execution  # noqa: E402
