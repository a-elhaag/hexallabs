from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth import AuthUser, get_current_user
from app.llm.base import Message
from app.llm.factory import get_client

router = APIRouter(prefix="/api", tags=["prompt-forge"])

# ---------------------------------------------------------------------------
# Prompt Forge system prompt — CACHED (hexal-caching-rules).
# Azure OpenAI uses automatic prefix cache; this text is invariant across all
# Forge requests so it will be a stable prefix and will hit the cache after
# the first request.  The text is placed first in the messages list so the
# first 1024 tokens are identical on every call.
# ---------------------------------------------------------------------------
_FORGE_SYSTEM_PROMPT = (
    "You are Prompt Forge, a query-improvement assistant embedded in Hexal."
    " Your job is to rewrite the user's raw query so it is clearer, more"
    " specific, and more answerable by a panel of AI models.\n\n"
    "Rules:\n"
    "1. Preserve the original intent and subject matter exactly — do NOT"
    " change what the user is asking about.\n"
    "2. Remove ambiguity: resolve vague pronouns, specify scope, add"
    " constraints where helpful.\n"
    "3. Sharpen the ask: if the user wants a comparison, say so; if they"
    " want step-by-step instructions, say so.\n"
    "4. Keep the improved query concise — one to three sentences maximum.\n"
    "5. Output ONLY the improved query text. No preamble, no explanation,"
    " no quotation marks around the result."
)


class ForgeRequest(BaseModel):
    query: str = Field(min_length=1)


class ForgeResponse(BaseModel):
    original: str
    improved: str


@router.post("/prompt-forge", response_model=ForgeResponse)
async def prompt_forge(
    req: ForgeRequest,
    user: AuthUser = Depends(get_current_user),  # noqa: B008
) -> ForgeResponse:
    """Rewrite a raw user query for clarity and specificity (non-streaming)."""
    try:
        client = get_client("Spark")
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e

    messages: list[Message] = [
        # System prompt is invariant → cache=True so Azure prefix cache applies.
        Message(role="system", content=_FORGE_SYSTEM_PROMPT, cache=True),
        # User query is dynamic per request → no cache.
        Message(role="user", content=req.query),
    ]

    collected: list[str] = []
    async for chunk in client.stream(messages):
        if chunk.delta:
            collected.append(chunk.delta)

    improved = "".join(collected).strip()
    if not improved:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Forge model returned an empty response.",
        )

    return ForgeResponse(original=req.query, improved=improved)
