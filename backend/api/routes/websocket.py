from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.core.websocket_manager import manager

router = APIRouter(prefix="/ws")

@router.websocket("/live/{client_id}")
async def ws_live(ws: WebSocket, client_id: str):
    channel = "live"
    await manager.connect(ws, client_id, channel)
    await ws.send_json({"type": "connected", "client_id": client_id, "source": "LIVE"})
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(client_id, channel)
