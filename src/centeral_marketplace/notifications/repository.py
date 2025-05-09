import json
import os
from upstash_redis import Redis
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import logging
import asyncio
from config import settings

logger = logging.getLogger(__name__)

class NotificationRepository:
    """Repository for handling notification storage and retrieval."""
    
    def __init__(self):
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
        
        self.notification_ttl = 7 * 24 * 60 * 60  # 7 days in seconds
        self._initialized = False
        self._connection_lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize Redis connection if needed."""
        async with self._connection_lock:
            if not self._initialized:
                logger.debug("Initializing NotificationRepository")
                try:
                    # Configure Redis using Upstash client
                    self.redis = Redis(url=self.redis_url, token=self.redis_token)
                    # Test connection
                    self.redis.ping()
                    self._initialized = True
                    logger.debug("NotificationRepository initialized")
                except Exception as e:
                    logger.error(f"Failed to initialize Redis connection: {e}")
                    self.redis = None
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
    
    async def save(self, notification: Dict[str, Any]) -> bool:
        """Save a notification to Redis."""
        try:
            await self.ensure_connection()
                
            user_id = notification.get("user_id")
            if not user_id:
                logger.error("Cannot save notification without user_id")
                return False
                
            notification_id = notification.get("id")
            if not notification_id:
                logger.error("Cannot save notification without id")
                return False
                
            # Store the notification with TTL
            key = f"notification:{notification_id}"
            notification_json = json.dumps(notification)
            self.redis.set(key, notification_json, ex=self.notification_ttl)
            
            # Add to user's notifications set
            user_key = f"user:{user_id}:notifications"
            self.redis.sadd(user_key, notification_id)
            
            logger.debug(f"Saved notification {notification_id} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving notification: {e}")
            return False
    
    async def mark_as_read(self, notification_id: str) -> bool:
        """Mark a notification as read."""
        try:
            await self.ensure_connection()
                
            key = f"notification:{notification_id}"
            notification_json = self.redis.get(key)
            if not notification_json:
                logger.warning(f"Notification {notification_id} not found")
                return False
                
            notification = json.loads(notification_json)
            notification["read"] = True
            notification["read_at"] = datetime.now(timezone.utc).isoformat()
            
            # Update notification with new TTL
            self.redis.set(
                key, 
                json.dumps(notification), 
                ex=self.notification_ttl
            )
            
            logger.debug(f"Marked notification {notification_id} as read")
            return True
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False
    
    async def get_user_notifications(
        self, 
        user_id: str, 
        limit: int = 20, 
        offset: int = 0,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get notifications for a user."""
        try:
            await self.ensure_connection()
                
            user_key = f"user:{user_id}:notifications"
            notification_ids = self.redis.smembers(user_key)
            
            if not notification_ids:
                logger.debug(f"No notifications found for user {user_id}")
                return []
                
            # Get all notifications data
            notifications = []
            
            for notification_id in notification_ids:
                key = f"notification:{notification_id}"
                notification_json = self.redis.get(key)
                if notification_json:
                    notification = json.loads(notification_json)
                    # Filter by read status if needed
                    if unread_only and notification.get("read", False):
                        continue
                    notifications.append(notification)
            
            # Sort by created_at in descending order (newest first)
            notifications.sort(
                key=lambda x: x.get("created_at", ""),
                reverse=True
            )
            
            # Apply pagination
            paginated = notifications[offset:offset + limit]
            
            logger.debug(f"Retrieved {len(paginated)} notifications for user {user_id}")
            return paginated
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return []

    async def close(self):
        """Close Redis connection."""
        self.redis = None
        self._initialized = False 