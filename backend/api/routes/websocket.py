from fastapi import APIRouter, WebSocket
router = APIRouter(prefix="/ws")
@router.websocket("/live/{client_id}")
async def ws_live(ws: WebSocket, client_id: str):
    await ws.accept()