import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for creating and managing notifications."""
    
    def __init__(self, repository):
        self.repository = repository
        self._initialized = False
        
    async def ensure_initialized(self):
        """Ensure the repository is initialized."""
        if not self._initialized:
            await self.repository.initialize()
            self._initialized = True
        
    async def create_notification(
        self, 
        user_id: str, 
        notification_type: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new notification for a user.
        
        Args:
            user_id: ID of the user to notify
            notification_type: Type of notification (e.g., 'comment', 'like')
            data: Dict containing notification data
            
        Returns:
            The created notification
        """
        try:
            await self.ensure_initialized()
            
            notification_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            
            notification = {
                "id": notification_id,
                "user_id": user_id,
                "notification_type": notification_type,
                "data": data,
                "created_at": now,
                "read": False,
                "read_at": None
            }
            
            success = await self.repository.save(notification)
            if not success:
                logger.error(f"Failed to save notification for user {user_id}")
                return None
                
            logger.info(f"Created notification {notification_id} for user {user_id}")
            return notification
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            return None
        
    async def mark_as_read(self, notification_id: str) -> bool:
        """
        Mark a notification as read.
        
        Args:
            notification_id: ID of the notification to mark as read
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.ensure_initialized()
            
            success = await self.repository.mark_as_read(notification_id)
            if success:
                logger.info(f"Marked notification {notification_id} as read")
            else:
                logger.warning(f"Failed to mark notification {notification_id} as read")
            return success
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
        """
        Get notifications for a user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of notifications to return
            offset: Offset for pagination
            unread_only: If True, only return unread notifications
            
        Returns:
            List of notification objects
        """
        try:
            await self.ensure_initialized()
            
            notifications = await self.repository.get_user_notifications(
                user_id, 
                limit=limit, 
                offset=offset,
                unread_only=unread_only
            )
            
            logger.info(f"Retrieved {len(notifications)} notifications for user {user_id}")
            return notifications
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return [] 