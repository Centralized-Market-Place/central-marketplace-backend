from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

import logging
from fastapi import HTTPException, status
from injector import inject, singleton

from centeral_marketplace.infrastructure.json import Pagination, PaginatedResponse
from centeral_marketplace.notifications.core import Notification, NotificationType
from centeral_marketplace.notifications.repository import NotificationRepository
from core import PyObjectId

logger = logging.getLogger(__name__)


@inject
@singleton
@dataclass
class NotificationService:
    repository: NotificationRepository

    def create_notification(
        self,
        user_id: PyObjectId,
        content: str,
        notification_type: NotificationType,
        metadata: Dict[str, Any] = None,
    ) -> Notification:
        try:
            notification = Notification(
                user_id=user_id,
                content=content,
                notification_type=notification_type,
                metadata=metadata or {},
            )
            saved_notification = self.repository.save(notification)
            logger.info(
                f"Created notification {saved_notification.id} for user {user_id}"
            )
            return saved_notification
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create notification",
            )

    def mark_as_read(
        self, notification_id: PyObjectId, user_id: PyObjectId
    ) -> Notification:
        notification = self.get_notification(notification_id, user_id)

        if notification.read:
            return notification

        notification.read = True
        notification.read_at = datetime.utcnow()

        try:
            updated = self.repository.save(notification)
            logger.info(f"Marked notification {notification_id} as read")
            return updated
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to mark notification as read",
            )

    def get_user_notifications(
        self,
        user_id: PyObjectId,
        pagination: Optional[Pagination] = None,
        read_filter: Optional[bool] = None,
    ) -> PaginatedResponse[Notification]:
        criteria = {"user_id": user_id}
        if read_filter is not None:
            criteria["read"] = read_filter

        try:
            result = self.repository.find_all_by_dict(
                criteria=criteria,
                pagination=pagination,
                sort_by="created_at",
                sort_desc=True,
            )

            logger.info(
                f"Retrieved {len(result.items)} notifications for user {user_id}"
            )
            return result
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve notifications",
            )

    def get_notification(
        self, notification_id: PyObjectId, user_id: PyObjectId
    ) -> Notification:
        try:
            notification = self.repository.find_one(notification_id)
            if str(notification.user_id) != str(user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this notification",
                )
            return notification
        except ValueError:
            logger.error(f"Notification with ID {notification_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification with ID {notification_id} not found",
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Error getting notification {notification_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve notification",
            )

    def delete_notification(
        self, notification_id: PyObjectId, user_id: PyObjectId
    ) -> None:
        self.get_notification(notification_id, user_id)

        try:
            self.repository.delete_one(notification_id)
            logger.info(f"Deleted notification {notification_id}")
        except Exception as e:
            logger.error(f"Error deleting notification {notification_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete notification",
            )

    def delete_all_for_user(self, user_id: PyObjectId) -> int:
        try:
            count = self.repository.delete_by_dict({"user_id": user_id})
            logger.info(f"Deleted {count} notifications for user {user_id}")
            return count
        except Exception as e:
            logger.error(f"Error deleting notifications for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete notifications",
            )
