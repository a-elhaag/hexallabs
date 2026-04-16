"""
The Relay — mid-conversation model handoff.

WebSocket endpoint that accepts a conversation history and a target model,
then streams the continuation from the new model with full context preserved.

WS URL: /ws/relay?token=<jwt>&model=<deployment_name>&primal_protocol=<bool>
Client sends JSON: {"messages": [{"role": "user"|"assistant"|"system", "content": str}]}
Server streams:
  {"type": "context_compressed", "originalMessageCount": N, "compressedMessageCount": M, ...}  (optional)
  {"type": "token", "chunk": str}  ...
  {"type": "done", "model": str, "totalCost": float}
"""
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.database import AsyncSessionLocal
from app.services.auth import decode_token
from app.services import foundry
from app.services import context as ctx
from app.services.council import COST_PER_1K
from app.services.billing import log_and_deduct

router = APIRouter(tags=["relay"])

PRIMAL_PROTOCOL_SUFFIX = (
    "\n\nPrimal Protocol active — respond terse, direct, no filler. Fragments OK."
)


@router.websocket("/ws/relay")
async def relay_ws(
    websocket: WebSocket,
    token: str = Query(...),
    model: str = Query(...),
    primal_protocol: bool = Query(False),
) -> None:
    """
    Stream a relay response from `model` given a conversation history.

    Automatically compresses older turns into a context summary when the
    conversation exceeds the threshold, keeping token usage efficient.
    """
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()

    try:
        data = await websocket.receive_json()
        messages: list[dict] = data.get("messages", [])

        if not messages:
            await websocket.send_json({"type": "error", "message": "No messages provided"})
            await websocket.close()
            return

        # Inject Primal Protocol into the system message if present
        if primal_protocol:
            if messages[0]["role"] == "system":
                messages[0]["content"] += PRIMAL_PROTOCOL_SUFFIX
            else:
                messages.insert(0, {"role": "system", "content": PRIMAL_PROTOCOL_SUFFIX.strip()})

        # Context compression — summarise older turns if token count is high
        compressed_messages, was_compressed, token_stats = await ctx.compress(messages)
        if was_compressed:
            await websocket.send_json(ctx.stats(token_stats))

        usage: dict = {}
        async for chunk in foundry.stream_chat(
            model=model,
            messages=compressed_messages,
            usage_out=usage,
        ):
            await websocket.send_json({"type": "token", "chunk": chunk})

        total_tokens = usage.get("total_tokens", 0)
        rate = COST_PER_1K.get(model, 0.0)
        total_cost = round(total_tokens / 1000 * rate, 6)

        if total_cost > 0:
            async with AsyncSessionLocal() as db:
                await log_and_deduct(
                    db=db,
                    user_id=payload.sub,
                    execution_id=None,
                    model_usage={model: usage},
                    cost_breakdown={model: total_cost},
                )

        await websocket.send_json({
            "type": "done",
            "model": model,
            "totalCost": total_cost,
        })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close()
