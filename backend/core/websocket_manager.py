from typing import Dict
class ConnectionManager:
    def __init__(self):
        self.active_connections = {}
    async def connect(self, websocket, client_id, channel):
        pass
    async def disconnect(self, client_id, channel):
        pass
    async def broadcast(self, channel, message):
        pass
    async def send_personal(self, client_id, message):
        pass
manager = ConnectionManager()