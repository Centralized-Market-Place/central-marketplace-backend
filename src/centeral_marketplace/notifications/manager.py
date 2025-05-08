import json
import os
import redis.asyncio as redis
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket
from injector import inject, singleton
import asyncio
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@singleton
class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.redis = None
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.channel = "notifications"
        self.pubsub = None
        self._listener_task = None
        self._initialized = False
        self._ping_interval = 30  # seconds
        self._ping_tasks = {}     # Track ping tasks per user
        self._connection_lock = asyncio.Lock()
        logger.debug("WebSocketManager initialized")

    async def initialize(self):
        """Initialize Redis connection and subscribe to notification channel."""
        async with self._connection_lock:
            if not self._initialized:
                logger.debug("Initializing WebSocketManager")
                try:
                    self.redis = redis.from_url(self.redis_url, decode_responses=True)
                    await self.redis.ping()  # Verify connection
                    self.pubsub = self.redis.pubsub()
                    await self.pubsub.subscribe(self.channel)
                    self._initialized = True
                    logger.debug("WebSocketManager initialization complete")
                except Exception as e:
                    logger.error(f"Failed to initialize WebSocketManager: {e}")
                    if self.redis:
                        await self.redis.close()
                        self.redis = None
                    if self.pubsub:
                        await self.pubsub.close()
                        self.pubsub = None
                    self._initialized = False
                    raise

    async def ensure_connection(self):
        """Ensure Redis connection is available."""
        if not self._initialized or not self.redis:
            await self.initialize()
        try:
            await self.redis.ping()
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
        
        # Ensure notification listener is running
        if not self._listener_task or self._listener_task.done():
            logger.debug("Starting notification listener task")
            self._listener_task = asyncio.create_task(self.listen_for_notifications())

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
        """Send a notification directly to a user (for testing)."""
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

    async def listen_for_notifications(self):
        """Listen for notifications from Redis and forward them to connected users."""
        await self.ensure_connection()
            
        logger.debug("Starting notification listener loop")
        retry_count = 0
        max_retries = 3
        
        while True:
            try:
                if retry_count > 0:
                    logger.debug(f"Retrying notification listener (attempt {retry_count}/{max_retries})")
                    
                message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                retry_count = 0  # Reset retry counter on successful receive
                
                if message and message["type"] == "message":
                    try:
                        notification_data = message["data"]
                        notification = json.loads(notification_data)
                        user_id = notification["user_id"]
                        logger.debug(f"Received notification for user {user_id}")
                        
                        success = await self.send_personal_message(user_id, notification_data)
                        if success:
                            logger.debug(f"Notification delivered to user {user_id}")
                        else:
                            logger.warning(f"Failed to deliver notification to user {user_id}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding notification: {e}")
                    except KeyError as e:
                        logger.error(f"Invalid notification format (missing key {e})")
                    except Exception as e:
                        logger.error(f"Error processing notification: {e}")
                        
                await asyncio.sleep(0.01)  # Small sleep to prevent CPU spinning
                
            except asyncio.CancelledError:
                logger.info("Notification listener task canceled")
                break
            except Exception as e:
                logger.error(f"Error in notification listener: {e}")
                retry_count += 1
                
                if retry_count > max_retries:
                    logger.critical(f"Too many errors in notification listener, resubscribing")
                    try:
                        # Resubscribe to channel
                        await self.pubsub.unsubscribe()
                        await self.pubsub.subscribe(self.channel)
                        retry_count = 0
                    except Exception as sub_error:
                        logger.error(f"Error resubscribing to channel: {sub_error}")
                        await asyncio.sleep(1)  # Wait before retrying
                        
                await asyncio.sleep(1)  # Longer sleep on errors

    async def close(self):
        """Close all connections and clean up resources."""
        logger.debug("Closing WebSocketManager")
        
        # Cancel all ping tasks
        for user_id, task in list(self._ping_tasks.items()):
            if not task.done():
                task.cancel()
                
        self._ping_tasks.clear()
        
        # Cancel listener task
        if self._listener_task and not self._listener_task.done():
            logger.debug("Canceling notification listener task")
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        
        # Close Redis connections
        if self.redis:
            logger.debug("Closing Redis connections")
            if self.pubsub:
                await self.pubsub.unsubscribe()
                await self.pubsub.close()
            await self.redis.close()
            self.redis = None
            self.pubsub = None
        
        # Close all WebSocket connections
        for user_id in list(self.active_connections.keys()):
            await self.disconnect(user_id)
            
        # Clear connections
        self.active_connections.clear()
        self._initialized = False
        logger.debug("WebSocketManager closed")

manager = WebSocketManager() 