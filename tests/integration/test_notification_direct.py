import pytest
import asyncio
import json
import os
import redis.asyncio as redis
import pytest_asyncio
import logging
import time
from src.centeral_marketplace.notifications.repository import NotificationRepository
from src.centeral_marketplace.notifications.service import NotificationService

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

@pytest_asyncio.fixture
async def redis_client():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    logger.debug(f"Connecting to Redis at {redis_url}")
    client = redis.from_url(redis_url, decode_responses=True)
    await client.flushdb()
    logger.debug("Redis database flushed")
    yield client
    await client.flushdb()
    await client.aclose()

@pytest_asyncio.fixture
async def notification_repository(redis_client):
    repo = NotificationRepository()
    repo.redis = redis_client
    await repo.initialize()
    yield repo

@pytest_asyncio.fixture
async def notification_service(notification_repository):
    service = NotificationService(notification_repository)
    yield service

@pytest_asyncio.fixture
async def redis_subscriber(redis_client):
    """Create a Redis pubsub subscriber for testing."""
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("notifications")
    yield pubsub
    await pubsub.unsubscribe()
    await pubsub.aclose()

@pytest.mark.asyncio
async def test_notification_creation(notification_service):
    """Test creating a notification."""
    user_id = "test_user"
    notification_type = "test_type"
    data = {"message": "Test notification"}
    
    # Create notification
    notification = await notification_service.create_notification(
        user_id, notification_type, data
    )
    
    # Verify notification
    assert notification is not None
    assert notification["user_id"] == user_id
    assert notification["notification_type"] == notification_type
    assert notification["data"] == data
    assert notification["read"] is False
    assert "id" in notification
    assert "created_at" in notification

@pytest.mark.asyncio
async def test_notification_persistence(notification_service):
    """Test that notifications are persisted and can be retrieved."""
    user_id = "test_user"
    
    # Create a few notifications
    for i in range(3):
        await notification_service.create_notification(
            user_id,
            f"type_{i}",
            {"message": f"Test notification {i}"}
        )
    
    # Retrieve notifications
    notifications = await notification_service.get_user_notifications(user_id)
    
    # Verify notifications
    assert len(notifications) == 3
    types = [n["notification_type"] for n in notifications]
    assert "type_0" in types
    assert "type_1" in types
    assert "type_2" in types

@pytest.mark.asyncio
async def test_notification_mark_as_read(notification_service):
    """Test marking a notification as read."""
    user_id = "test_user"
    
    # Create a notification
    notification = await notification_service.create_notification(
        user_id, "test_type", {"message": "Test notification"}
    )
    
    notification_id = notification["id"]
    
    # Mark as read
    success = await notification_service.mark_as_read(notification_id)
    assert success is True
    
    # Verify notification is marked as read
    notifications = await notification_service.get_user_notifications(user_id)
    assert len(notifications) == 1
    assert notifications[0]["read"] is True
    assert notifications[0]["read_at"] is not None

@pytest.mark.asyncio
async def test_notification_publishing(notification_service, redis_subscriber):
    """Test that notifications are published to Redis channel."""
    user_id = "test_user"
    notification_type = "test_type"
    data = {"message": "Test notification"}
    
    # Create a notification
    notification = await notification_service.create_notification(
        user_id, notification_type, data
    )
    
    # Check that notification was published
    message = None
    start_time = time.time()
    timeout = 3.0
    
    while time.time() - start_time < timeout and not message:
        message = await redis_subscriber.get_message(ignore_subscribe_messages=True, timeout=0.1)
        if not message:
            await asyncio.sleep(0.1)
    
    assert message is not None, "No message published to Redis"
    assert message["type"] == "message"
    assert message["channel"] == "notifications"
    
    # Parse the message data
    published_notification = json.loads(message["data"])
    assert published_notification["user_id"] == user_id
    assert published_notification["notification_type"] == notification_type
    assert published_notification["data"]["message"] == "Test notification" 