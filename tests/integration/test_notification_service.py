import pytest
import redis.asyncio as redis
import os
from src.centeral_marketplace.notifications.service import NotificationService
from src.centeral_marketplace.notifications.repository import NotificationRepository
from src.centeral_marketplace.notifications.core import Notification
import pytest_asyncio

@pytest_asyncio.fixture
async def redis_client():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    client = redis.from_url(redis_url, decode_responses=True)
    # Clear all keys in Redis before the test
    await client.flushall()
    yield client
    # Clean up after test
    await client.flushall()
    await client.aclose()

@pytest_asyncio.fixture
async def notification_repository(redis_client):
    repo = NotificationRepository()
    await repo.initialize()
    yield repo
    await repo.close()

@pytest_asyncio.fixture
async def notification_service(notification_repository):
    service = NotificationService(notification_repository)
    yield service
    await service.cleanup()

@pytest.mark.asyncio
async def test_notification_flow(notification_service):
    # Create a notification
    user_id = "test_user"
    notification_type = "test_type"
    data = {"message": "Test notification"}
    notification = await notification_service.create_notification(user_id, notification_type, data)
    assert notification.user_id == user_id
    assert notification.notification_type == notification_type
    assert notification.data == data
    assert not notification.read

    # Retrieve notifications for the user
    notifications = await notification_service.get_user_notifications(user_id)
    assert len(notifications) == 1
    assert notifications[0].id == notification.id

    # Mark the notification as read
    updated_notification = await notification_service.mark_as_read(notification.id, user_id)
    assert updated_notification.read

    # Verify the notification is marked as read
    notifications = await notification_service.get_user_notifications(user_id)
    assert notifications[0].read

@pytest.mark.asyncio
async def test_multiple_notifications(notification_service):
    user_id = "test_user"
    notifications = []
    
    # Create multiple notifications
    for i in range(3):
        notification = await notification_service.create_notification(
            user_id,
            f"type_{i}",
            {"message": f"Test notification {i}"}
        )
        notifications.append(notification)
    
    # Verify all notifications are retrieved
    retrieved = await notification_service.get_user_notifications(user_id)
    assert len(retrieved) == 3
    
    # Verify notifications are in correct order (newest first)
    assert retrieved[0].id == notifications[2].id
    assert retrieved[1].id == notifications[1].id
    assert retrieved[2].id == notifications[0].id

@pytest.mark.asyncio
async def test_notification_pagination(notification_service):
    user_id = "test_user"
    
    # Create 5 notifications
    for i in range(5):
        await notification_service.create_notification(
            user_id,
            "test_type",
            {"message": f"Test notification {i}"}
        )
    
    # Test limit of 3
    notifications = await notification_service.get_user_notifications(user_id, limit=3)
    assert len(notifications) == 3

@pytest.mark.asyncio
async def test_mark_nonexistent_notification(notification_service):
    # Try to mark a non-existent notification as read
    result = await notification_service.mark_as_read("nonexistent_id", "test_user")
    assert result is None

@pytest.mark.asyncio
async def test_get_notifications_for_nonexistent_user(notification_service):
    # Get notifications for a user that has none
    notifications = await notification_service.get_user_notifications("nonexistent_user")
    assert len(notifications) == 0 