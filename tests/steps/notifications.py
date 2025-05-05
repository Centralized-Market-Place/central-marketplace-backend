from centeral_marketplace.notifications.repository import NotificationRepository
from centeral_marketplace.notifications.service import NotificationService
from centeral_marketplace.notifications.core import Notification
from centeral_marketplace.users.core import User
from tests.core.notifications import create_test_notification
from centeral_marketplace.shared.interfaces import IProductService, ICommentService
from injector import Module, provider, singleton, Binder

# Test step functions for notifications
def notification_repository_is_ready():
    def step(context):
        context.notification_repository = NotificationRepository()
        
    return step

def notification_service_is_ready(product_service=None, comment_service=None):
    def step(context):
        if not hasattr(context, 'notification_repository'):
            context.notification_repository = NotificationRepository()
            
        context.notification_service = NotificationService(
            notification_repository=context.notification_repository,
            product_service=product_service or context.injector.get(IProductService),
            comment_service=comment_service or context.injector.get(ICommentService)
        )
        
    return step

def there_is_a_notification(user_id, notification_type="test", data=None):
    async def step(context):
        if not hasattr(context, 'notification_repository'):
            context.notification_repository = NotificationRepository()
            await context.notification_repository.initialize()
            
        notification = await create_test_notification(user_id, notification_type, data)
        saved_notification = await context.notification_repository.save(notification)
        context.notification = saved_notification
        return saved_notification
        
    return step

# Module for testing
class TestNotificationsModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(NotificationRepository, to=NotificationRepository, scope=singleton)
        
    @provider
    @singleton
    def provide_notification_service(
        self, 
        notification_repository: NotificationRepository,
        product_service: IProductService,
        comment_service: ICommentService
    ) -> NotificationService:
        return NotificationService(
            notification_repository=notification_repository,
            product_service=product_service,
            comment_service=comment_service
        ) 