import json
import os
from upstash_redis import Redis
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket
from injector import inject, singleton
import asyncio
import logging
from datetime import datetime
from config import settings

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@singleton
class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.redis = None
        # Parse Redis URL to get components for Upstash
        redis_url = settings.redis_url.replace("redis://", "")
        if "@" in redis_url:
            auth, rest = redis_url.split("@")
            _, password = auth.split(":")
            host, _ = rest.split(":")
            self.redis_url = f"https://{host}"
            self.redis_token = password
        else:
            self.redis_url = f"https://{redis_url.split(':')[0]}"
            self.redis_token = ""
        
        self.channel = "notifications"
        self._initialized = False
        self._ping_interval = 30  # seconds
        self._ping_tasks = {}     # Track ping tasks per user
        self._connection_lock = asyncio.Lock()
        logger.debug("WebSocketManager initialized")

    async def initialize(self):
        """Initialize Redis connection."""
        async with self._connection_lock:
            if not self._initialized:
                logger.debug("Initializing WebSocketManager")
                try:
                    # Configure Redis using Upstash client
                    self.redis = Redis(url=self.redis_url, token=self.redis_token)
                    # Test connection
                    self.redis.ping()
                    self._initialized = True
                    logger.debug("WebSocketManager initialization complete")
                except Exception as e:
                    logger.error(f"Failed to initialize WebSocketManager: {e}")
                    self.redis = None
                    self._initialized = False
                    raise

    async def ensure_connection(self):
        """Ensure Redis connection is available."""
        if not self._initialized or not self.redis:
            await self.initialize()
        try:
            self.redis.ping()
        except Exception as e:
            logger.error(f"Redis connection lost: {e}")
            self._initialized = False
            await self.initialize()

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a new WebSocket connection for a user."""
        logger.debug(f"New WebSocket connection request from user {user_id}")
        await self.ensure_connection()
            
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.debug(f"WebSocket connection accepted for user {user_id}")
        
        # Start ping/pong task for this connection
        self._ping_tasks[user_id] = asyncio.create_task(self._keep_alive(user_id))

    async def _keep_alive(self, user_id: str):
        """Keep the connection alive with ping/pong messages."""
        try:
            while user_id in self.active_connections:
                await asyncio.sleep(self._ping_interval)
                if user_id in self.active_connections:
                    try:
                        await self.active_connections[user_id].send_text("ping")
                        logger.debug(f"Sent ping to user {user_id}")
                    except Exception as e:
                        logger.error(f"Error in keep-alive for user {user_id}: {e}")
                        await self.disconnect(user_id)
                        break
        except asyncio.CancelledError:
            logger.debug(f"Keep-alive task canceled for user {user_id}")
        except Exception as e:
            logger.error(f"Unexpected error in keep-alive task for {user_id}: {e}")
            await self.disconnect(user_id)

    async def disconnect(self, user_id: str):
        """Disconnect a user's WebSocket connection."""
        if user_id in self.active_connections:
            logger.debug(f"Disconnecting user {user_id}")
            
            # Cancel ping task if exists
            if user_id in self._ping_tasks and not self._ping_tasks[user_id].done():
                self._ping_tasks[user_id].cancel()
                del self._ping_tasks[user_id]
                
            try:
                await self.active_connections[user_id].close()
            except Exception as e:
                logger.error(f"Error closing WebSocket for user {user_id}: {e}")
                
            del self.active_connections[user_id]
            logger.debug(f"User {user_id} disconnected, {len(self.active_connections)} connections remaining")

    async def send_personal_message(self, user_id: str, message: str):
        """Send a message to a specific user."""
        if user_id in self.active_connections:
            try:
                logger.debug(f"Sending message to user {user_id}: {message[:100]}...")
                await self.active_connections[user_id].send_text(message)
                return True
            except Exception as e:
                logger.error(f"Error sending message to {user_id}: {e}")
                await self.disconnect(user_id)
                return False
        return False
    
    async def send_notification_to_user(self, user_id: str, notification: Dict[str, Any]):
        """Send a notification directly to a user."""
        if not user_id in self.active_connections:
            logger.warning(f"No active connection for user {user_id}")
            return False
            
        try:
            notification_json = json.dumps(notification)
            logger.debug(f"Sending notification directly to user {user_id}")
            await self.active_connections[user_id].send_text(notification_json)
            return True
        except Exception as e:
            logger.error(f"Error sending direct notification to {user_id}: {e}")
            await self.disconnect(user_id)
            return False

    async def broadcast(self, message: str):
        """Broadcast a message to all connected users."""
        logger.debug(f"Broadcasting message to {len(self.active_connections)} connections")
        disconnected = []
        sent_count = 0
        
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message)
                sent_count += 1
            except Exception as e:
                logger.error(f"Error broadcasting to {user_id}: {e}")
                disconnected.append(user_id)
        
        for user_id in disconnected:
            await self.disconnect(user_id)
            
        logger.debug(f"Broadcast complete: {sent_count} messages sent, {len(disconnected)} connections closed")
        return sent_count

    async def close(self):
        """Close all connections and clean up resources."""
        logger.debug("Closing WebSocketManager")
        
        # Cancel all ping tasks
        for user_id, task in list(self._ping_tasks.items()):
            if not task.done():
                task.cancel()
                
        self._ping_tasks.clear()
        
        # Close all WebSocket connections
        for user_id in list(self.active_connections.keys()):
            await self.disconnect(user_id)
            
        # Clear connections
        self.active_connections.clear()
        self._initialized = False
        logger.debug("WebSocketManager closed")

manager = WebSocketManager() 