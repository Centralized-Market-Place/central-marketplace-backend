import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from src.centeral_marketplace.notifications.core import Notification
from src.centeral_marketplace.notifications.service import NotificationService
from src.centeral_marketplace.notifications.repository import NotificationRepository
import pytest_asyncio
import os
import redis.asyncio as redis
import logging
import time
from contextlib import contextmanager

# Configure logging to see debug messages
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@contextmanager
def websocket_connect(client: TestClient, url: str, timeout=0.5):
    logger.debug(f"Connecting to WebSocket at {url}")
    websocket = client.websocket_connect(url)
    try:
        logger.debug("WebSocket connection established")
        yield websocket
    finally:
        logger.debug("Closing WebSocket connection")
        websocket.close()

@pytest_asyncio.fixture
async def redis_client():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    logger.debug(f"Connecting to Redis at {redis_url}")
    client = redis.from_url(redis_url, decode_responses=True)
    await client.flushdb()
    logger.debug("Redis database flushed before test")
    yield client
    await client.flushdb()
    logger.debug("Redis database flushed after test")
    await client.aclose()

@pytest_asyncio.fixture
async def notification_repository(redis_client):
    logger.debug("Creating notification repository for test")
    repo = NotificationRepository()
    repo.redis = redis_client
    await repo.initialize()  # Ensure repository is initialized
    logger.debug("Notification repository initialized")
    yield repo

@pytest_asyncio.fixture
async def notification_service(notification_repository):
    logger.debug("Creating notification service for test")
    service = NotificationService(notification_repository)
    yield service

@pytest_asyncio.fixture
async def test_client():
    logger.debug("Creating test client")
    from src.centeral_marketplace.main import app
    client = TestClient(app)
    yield client

@pytest.mark.asyncio
async def test_websocket_connection(test_client):
    """Test basic WebSocket connection and authentication."""
    user_id = "test_user"
    websocket_url = f"/api/v1/notifications/ws?user_id={user_id}"
    
    logger.debug(f"Testing WebSocket connection for user {user_id}")
    with websocket_connect(test_client, websocket_url) as websocket:
        assert websocket is not None
        await asyncio.sleep(0.5)  # Wait to ensure connection is established
    logger.debug("WebSocket connection test complete")

@pytest.mark.asyncio
async def test_websocket_notification_delivery(test_client, notification_service):
    """Test that notifications are delivered through WebSocket."""
    user_id = "test_user"
    websocket_url = f"/api/v1/notifications/ws?user_id={user_id}"
    
    logger.debug(f"Testing notification delivery for user {user_id}")
    with websocket_connect(test_client, websocket_url) as websocket:
        # Wait for connection to be established
        logger.debug("Waiting for connection to be established")
        await asyncio.sleep(0.5)
        
        # Create a notification
        logger.debug("Creating test notification")
        notification = await notification_service.create_notification(
            user_id,
            "test_type",
            {"message": "Test notification"}
        )
        logger.debug(f"Created notification: {notification}")
        
        # Wait for the notification to be delivered
        received_data = None
        start_time = time.time()
        timeout = 5.0  # 5 seconds timeout
        
        logger.debug(f"Waiting up to {timeout} seconds for notification to be delivered")
        while time.time() - start_time < timeout and not received_data:
            # Process any pending ping/pong messages
            try:
                logger.debug("Trying to receive WebSocket message")
                data = websocket.receive_text(timeout=0.1)
                logger.debug(f"Received message: {data}")
                
                if data == "ping":
                    websocket.send_text("pong")
                    logger.debug("Received ping, sent pong")
                    continue
                elif data == "pong":
                    logger.debug("Received pong")
                    continue
                
                # Real notification data received
                received_data = json.loads(data)
                logger.debug(f"Received notification: {received_data}")
                break
            except Exception as e:
                logger.debug(f"Waiting for notification, no data yet: {e}")
                await asyncio.sleep(0.1)
        
        # Print channel message count for debugging
        if hasattr(notification_service.repository.redis, 'pubsub_numsub'):
            try:
                # Check if anyone is subscribed to the notifications channel
                subs = await notification_service.repository.redis.pubsub_numsub('notifications')
                logger.debug(f"Subscribers to notifications channel: {subs}")
            except Exception as e:
                logger.debug(f"Failed to check subscribers: {e}")
        
        # Verify notification content
        assert received_data is not None, "No notification received within timeout"
        assert received_data["user_id"] == user_id
        assert received_data["notification_type"] == "test_type"
        assert received_data["data"]["message"] == "Test notification"
        
        logger.debug("Notification delivery test complete")

@pytest.mark.asyncio
async def test_websocket_multiple_notifications(test_client, notification_service):
    """Test handling of multiple notifications through WebSocket."""
    user_id = "test_user"
    websocket_url = f"/api/v1/notifications/ws?user_id={user_id}"
    
    logger.debug(f"Testing multiple notifications for user {user_id}")
    with websocket_connect(test_client, websocket_url) as websocket:
        # Wait for connection to be established
        logger.debug("Waiting for connection to be established")
        await asyncio.sleep(0.5)
        
        # Create multiple notifications
        logger.debug("Creating multiple test notifications")
        for i in range(3):
            notification = await notification_service.create_notification(
                user_id,
                f"type_{i}",
                {"message": f"Test notification {i}"}
            )
            logger.debug(f"Created notification {i}: {notification}")
            await asyncio.sleep(0.2)  # Small delay between notifications
        
        # Collect notifications
        received_notifications = []
        start_time = time.time()
        timeout = 5.0  # 5 seconds timeout
        
        logger.debug(f"Waiting up to {timeout} seconds for notifications to be delivered")
        while time.time() - start_time < timeout and len(received_notifications) < 3:
            try:
                logger.debug("Trying to receive WebSocket message")
                data = websocket.receive_text(timeout=0.2)
                logger.debug(f"Received message: {data}")
                
                if data == "ping":
                    websocket.send_text("pong")
                    logger.debug("Received ping, sent pong")
                    continue
                elif data == "pong":
                    logger.debug("Received pong")
                    continue
                
                notification = json.loads(data)
                logger.debug(f"Received notification: {notification}")
                received_notifications.append(notification)
            except Exception as e:
                logger.debug(f"Waiting for notifications, have {len(received_notifications)} so far: {e}")
                await asyncio.sleep(0.1)
        
        # Verify all notifications
        assert len(received_notifications) == 3, f"Expected 3 notifications, got {len(received_notifications)}"
        types = sorted([n["notification_type"] for n in received_notifications])
        assert types == ["type_0", "type_1", "type_2"]
        
        logger.debug("Multiple notifications test complete")

@pytest.mark.asyncio
async def test_websocket_authentication_failure(test_client):
    """Test WebSocket connection rejection when no authentication is provided."""
    websocket_url = "/api/v1/notifications/ws"
    
    logger.debug("Testing WebSocket authentication failure")
    # Attempt to connect without authentication
    with pytest.raises(Exception) as exc_info:
        with test_client.websocket_connect(websocket_url) as websocket:
            pass
    
    assert "Policy violation" in str(exc_info.value)
    logger.debug("Authentication failure test complete") 