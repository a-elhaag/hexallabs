from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CouncilConfigCreate(BaseModel):
    name: str
    models: list[str] = Field(
        default=["gpt-5.1-chat", "DeepSeek-V3.2-Speciale", "Llama-3.3-70B-Instruct", "Kimi-K2.5"]
    )
    system_prompt: str
    organizer_model: Optional[str] = Field(default="gpt-5.4-mini")


class CouncilConfigResponse(BaseModel):
    id: str
    user_id: str
    name: str
    models: list[str]
    system_prompt: str
    organizer_model: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ExecuteRequest(BaseModel):
    council_id: str
    query: str
    user_id: str


class ExecuteResponse(BaseModel):
    execution_id: str
    status: str
