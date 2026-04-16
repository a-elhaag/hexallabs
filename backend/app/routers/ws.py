from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.database import AsyncSessionLocal
from app.services.auth import decode_token
from app.services import council as council_service

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def council_ws(
    websocket: WebSocket,
    execution_id: str = Query(...),
    token: str = Query(...),
    scout_enabled: bool = Query(False),
    primal_protocol: bool = Query(False),
):
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()

    async with AsyncSessionLocal() as db:
        try:
            async for event in council_service.run_council(
                db,
                execution_id,
                payload.sub,
                scout_enabled=scout_enabled,
                primal_protocol=primal_protocol,
            ):
                await websocket.send_json(event)
        except WebSocketDisconnect:
            pass
        except Exception as e:
            await websocket.send_json({"type": "error", "message": str(e)})
            await websocket.close()
