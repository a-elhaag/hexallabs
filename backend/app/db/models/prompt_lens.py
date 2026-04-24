from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models._common import created_at_col, uuid_pk


class PromptLensEntry(Base):
    __tablename__ = "prompt_lens_entries"

    id: Mapped[uuid.UUID] = uuid_pk()
    query_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("queries.id", ondelete="CASCADE"),
        nullable=False,
    )
    model: Mapped[str] = mapped_column(String, nullable=False)
    interpretation: Mapped[str] = mapped_column(String, nullable=False)
    divergence_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    created_at: Mapped[datetime] = created_at_col()
