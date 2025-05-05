import json
import os
import redis.asyncio as redis
from typing import Dict, Set
from fastapi import WebSocket
from injector import inject, singleton

@singleton
class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.redis = None
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.channel = "notifications"

    async def initialize(self):
        if not self.redis:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.subscribe(self.channel)
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe(self.channel)

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, user_id: str, message: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

    async def listen_for_notifications(self):
        await self.initialize()
        while True:
            message = await self.pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                notification = json.loads(message["data"])
                user_id = notification["user_id"]
                await self.send_personal_message(user_id, message["data"])

    async def close(self):
        if self.redis:
            await self.redis.close()
            await self.pubsub.close()

manager = WebSocketManager() 