import datetime
import json
from typing import List
from injector import inject, singleton
from .core import Notification
from .repository import NotificationRepository
from .manager import manager

@singleton
@inject
class NotificationService:
    def __init__(
        self,
        notification_repository: NotificationRepository
    ):
        self.notification_repository = notification_repository

    async def create_notification(
        self,
        user_id: str,
        notification_type: str,
        data: dict
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            data=data
        )
        return await self.notification_repository.save(notification)

    async def mark_as_read(self, notification_id: str, user_id: str) -> Notification:
        return await self.notification_repository.mark_as_read(notification_id, user_id)

    async def get_user_notifications(self, user_id: str, limit: int = 50) -> List[Notification]:
        return await self.notification_repository.get_user_notifications(user_id, limit)

    async def cleanup(self):
        await self.notification_repository.close() 