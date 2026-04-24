from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class PeerReview(BaseModel):
    score: float
    feedback: str


class ExecutionResponse(BaseModel):
    id: str
    council_id: str
    query: str
    status: str
    model_responses: dict[str, Any] | None = None
    peer_reviews: dict[str, Any] | None = None
    synthesis: str | None = None
    cost_breakdown: dict[str, float] | None = None
    workspace_kind: str | None = None
    artifact: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
