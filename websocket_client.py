import asyncio
import websockets
import json
import threading
from datetime import datetime

class WebSocketClient:
    def __init__(self):
        self.websocket = None
        self.loop = None
        self.thread = None
        self.connected = False

    def start(self):
        if not self.thread or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._run_client, daemon=True)
            self.thread.start()

    def _run_client(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._connect())

    async def _connect(self):
        try:
            self.websocket = await websockets.connect("ws://localhost:8765")
            self.connected = True
            await asyncio.Future()
        except Exception as e:
            self.connected = False

    def send_event(self, event_data):
        if self.connected and self.websocket and self.loop:
            asyncio.run_coroutine_threadsafe(
                self.websocket.send(json.dumps(event_data)),
                self.loop
            )

ws_client = WebSocketClient()