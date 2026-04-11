from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.services.auth import decode_token
from app.services import council as council_service

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def council_ws(
    websocket: WebSocket,
    execution_id: str = Query(...),
    token: str = Query(...),
):
    # Validate JWT before accepting the connection
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()

    async with AsyncSessionLocal() as db:
        try:
            async for event in council_service.run_council(db, execution_id, payload.sub):
                await websocket.send_json(event)
        except WebSocketDisconnect:
            pass
        except Exception as e:
            await websocket.send_json({"type": "error", "message": str(e)})
            await websocket.close()
