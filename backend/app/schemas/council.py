from datetime import datetime

from pydantic import BaseModel, Field


class CouncilConfigCreate(BaseModel):
    name: str
    models: list[str] = Field(
        default=["gpt-4o", "o1", "deepseek-r1", "mistral-large-3"]
    )
    system_prompt: str


class CouncilConfigResponse(BaseModel):
    id: str
    user_id: str
    name: str
    models: list[str]
    system_prompt: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ExecuteRequest(BaseModel):
    council_id: str
    query: str
    user_id: str


class ExecuteResponse(BaseModel):
    execution_id: str
    status: str
