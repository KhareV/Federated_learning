from typing import Dict


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, object] = {}

    async def connect(self, websocket, client_id, channel):
        await websocket.accept()
        self.active_connections[f"{channel}:{client_id}"] = websocket

    async def disconnect(self, client_id, channel):
        self.active_connections.pop(f"{channel}:{client_id}", None)

    async def broadcast(self, channel, message):
        for key, websocket in list(self.active_connections.items()):
            if key.startswith(f"{channel}:"):
                await websocket.send_json(message)

    async def send_personal(self, client_id, message):
        for key, websocket in list(self.active_connections.items()):
            if key.endswith(f":{client_id}"):
                await websocket.send_json(message)

manager = ConnectionManager()
