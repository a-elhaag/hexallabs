from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.debug import router as debug_router
from app.api.prompt_forge import router as forge_router
from app.api.query import router as query_router
from app.api.quota import router as quota_router
from app.auth.middleware import get_current_user
from app.auth.mock import mock_get_current_user
from app.config import get_settings
from app.db.session import dispose_engine

logger = logging.getLogger(__name__)


def _warn_missing_optional_config() -> None:
    """Emit startup warnings for missing optional config so operators know which
    features are degraded.  These are intentionally optional — do NOT raise."""
    settings = get_settings()

    if not settings.tavily_api_key:
        logger.warning(
            "TAVILY_API_KEY is not set — Scout (web search) is disabled. "
            "Set TAVILY_API_KEY to enable it."
        )

    if not settings.azure_foundry_api_key:
        logger.warning(
            "AZURE_FOUNDRY_API_KEY is not set — Azure AI Foundry calls will rely "
            "on managed identity / token auth. Set AZURE_FOUNDRY_API_KEY if using "
            "API-key authentication."
        )

    if not settings.models:
        logger.warning(
            "No model whitelabels are configured (MODEL_<NAME> + MODEL_<NAME>_PROVIDER "
            "env vars). At least one model is required to serve requests."
        )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    _warn_missing_optional_config()
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
app.include_router(quota_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
