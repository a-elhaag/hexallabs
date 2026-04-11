from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String)
    provider: Mapped[str | None] = mapped_column(String)
    provider_id: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    council_configs: Mapped[list[CouncilConfig]] = relationship(
        "CouncilConfig", back_populates="user", cascade="all, delete-orphan"
    )
    executions: Mapped[list[Execution]] = relationship(
        "Execution", back_populates="user"
    )


from app.models.council import CouncilConfig  # noqa: E402
from app.models.execution import Execution  # noqa: E402
