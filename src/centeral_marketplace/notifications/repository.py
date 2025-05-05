import json
import os
from typing import List
import redis.asyncio as redis
from injector import inject, singleton
from .core import Notification

@singleton
@inject
class NotificationRepository:
    def __init__(self):
        self.redis = None
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.notification_ttl = 7 * 24 * 60 * 60  # 7 days in seconds

    async def initialize(self):
        if not self.redis:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)

    async def save(self, notification: Notification) -> Notification:
        await self.initialize()
        notification_data = notification.model_dump_json()
        
        # Publish to channel for real-time delivery
        await self.redis.publish('notifications', notification_data)
        
        # Store in Redis for persistence with TTL
        key = f"notification:{notification.user_id}:{notification.id}"
        await self.redis.set(key, notification_data, ex=self.notification_ttl)
        return notification

    async def mark_as_read(self, notification_id: str, user_id: str) -> Notification:
        await self.initialize()
        key = f"notification:{user_id}:{notification_id}"
        notification_data = await self.redis.get(key)
        
        if notification_data:
            notification = Notification.model_validate_json(notification_data)
            notification.read = True
            # When marking as read, reset the TTL
            await self.redis.set(key, notification.model_dump_json(), ex=self.notification_ttl)
            return notification
        return None

    async def get_user_notifications(self, user_id: str, limit: int = 50) -> List[Notification]:
        await self.initialize()
        pattern = f"notification:{user_id}:*"
        keys = await self.redis.keys(pattern)
        notifications = []
        
        for key in keys:
            notification_data = await self.redis.get(key)
            if notification_data:
                notification = Notification.model_validate_json(notification_data)
                notifications.append(notification)
        
        # Sort notifications by creation time (newest first)
        notifications.sort(key=lambda x: x.created_at, reverse=True)
        return notifications[:limit]

    async def close(self):
        if self.redis:
            await self.redis.aclose() 