from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.debug import router as debug_router
from app.api.prompt_forge import router as forge_router
from app.api.query import router as query_router
from app.auth.middleware import get_current_user
from app.auth.mock import mock_get_current_user
from app.db.session import dispose_engine


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally:
        await dispose_engine()


app = FastAPI(title="Hexal-LM Backend", version="0.1.0", lifespan=lifespan)

# Use mock auth in dev mode (MOCK_AUTH=1)
if os.getenv("MOCK_AUTH") == "1":
    app.dependency_overrides[get_current_user] = mock_get_current_user

app.include_router(debug_router)
app.include_router(query_router)
app.include_router(forge_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
