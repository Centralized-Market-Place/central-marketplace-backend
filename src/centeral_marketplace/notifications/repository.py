import json
import os
import redis.asyncio as redis
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class NotificationRepository:
    """Repository for handling notification storage and retrieval."""
    
    def __init__(self):
        self.redis = None
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.notification_ttl = 7 * 24 * 60 * 60  # 7 days in seconds
        self._initialized = False
        
    async def initialize(self):
        """Initialize Redis connection if needed."""
        if not self._initialized:
            logger.debug("Initializing NotificationRepository")
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()  # Verify connection
            self._initialized = True
            logger.debug("NotificationRepository initialized")
    
    async def save(self, notification: Dict[str, Any]) -> bool:
        """Save a notification to Redis."""
        if not self.redis:
            await self.initialize()
            
        user_id = notification.get("user_id")
        if not user_id:
            logger.error("Cannot save notification without user_id")
            return False
            
        notification_id = notification.get("id")
        if not notification_id:
            logger.error("Cannot save notification without id")
            return False
            
        try:
            # Store the notification with TTL
            key = f"notification:{notification_id}"
            notification_json = json.dumps(notification)
            await self.redis.set(key, notification_json, ex=self.notification_ttl)
            
            # Add to user's notifications set
            user_key = f"user:{user_id}:notifications"
            await self.redis.sadd(user_key, notification_id)
            
            # Publish notification for real-time delivery
            channel = "notifications"
            await self.redis.publish(channel, notification_json)
            
            logger.debug(f"Saved and published notification {notification_id} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving notification: {e}")
            return False
    
    async def mark_as_read(self, notification_id: str) -> bool:
        """Mark a notification as read."""
        if not self.redis:
            await self.initialize()
            
        try:
            key = f"notification:{notification_id}"
            notification_json = await self.redis.get(key)
            if not notification_json:
                logger.warning(f"Notification {notification_id} not found")
                return False
                
            notification = json.loads(notification_json)
            notification["read"] = True
            notification["read_at"] = datetime.now(timezone.utc).isoformat()
            
            # Update notification with new TTL
            await self.redis.set(
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
        if not self.redis:
            await self.initialize()
            
        try:
            user_key = f"user:{user_id}:notifications"
            notification_ids = await self.redis.smembers(user_key)
            
            if not notification_ids:
                logger.debug(f"No notifications found for user {user_id}")
                return []
                
            # Get all notifications data
            notifications = []
            pipeline = self.redis.pipeline()
            
            for notification_id in notification_ids:
                key = f"notification:{notification_id}"
                pipeline.get(key)
                
            results = await pipeline.execute()
            
            for result in results:
                if result:
                    notification = json.loads(result)
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
        if self.redis:
            await self.redis.aclose() 