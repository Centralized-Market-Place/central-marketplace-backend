from centeral_marketplace.notifications.core import Notification, NotificationType
from centeral_marketplace.notifications.repository import NotificationRepository
from core import PyObjectId
from datetime import UTC, datetime


def there_is_a_notification(
    user_id: PyObjectId = None,
    content: str = "Test notification",
    notification_type: NotificationType = NotificationType.SYSTEM,
    read: bool = False,
    metadata: dict = None,
):
    def step(context):
        notification_repo: NotificationRepository = context.injector.get(NotificationRepository)
        
        actual_user_id = user_id or context.user.id
        
        notification = Notification(
            user_id=actual_user_id,
            content=content,
            notification_type=notification_type,
            read=read,
            metadata=metadata or {},
            read_at=datetime.now(UTC) if read else None
        )
        
        saved_notification = notification_repo.save(notification) 
        context.notification = saved_notification


    return step


def there_are_multiple_notifications(
    count: int = 5, 
    user_id: PyObjectId = None, 
    notification_type: NotificationType = NotificationType.SYSTEM
):
    def step(context):
        notification_repo: NotificationRepository = context.injector.get(NotificationRepository)
        actual_user_id = user_id or context.user.id

        notifications = []
        for i in range(count):
            is_read = i % 2 == 0
            
            notification = Notification(
                user_id=actual_user_id,
                content=f"Test notification {i+1}",
                notification_type=notification_type,
                read=is_read,
                metadata={"index": i},
                read_at=datetime.now(UTC) if is_read else None
            )
            
            saved_notification = notification_repo.save(notification)
            notifications.append(saved_notification)

        context.notifications = notifications
        context.read_notifications_count = sum(1 for n in notifications if n.read)
        context.unread_notifications_count = sum(1 for n in notifications if not n.read)
    
    return step
