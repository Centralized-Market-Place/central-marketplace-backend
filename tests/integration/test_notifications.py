import pytest
import asyncio
import websockets
import requests
import json
import logging
from datetime import datetime
import jwt

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8443/api/v1"
AUTH_URL = f"{BASE_URL}/users/login"
NOTIFICATIONS_URL = f"{BASE_URL}/notifications"
WS_URL = "ws://127.0.0.1:8443/api/v1/notifications/ws"

# Shared test data
class TestData:
    notification_id = None

@pytest.fixture
def test_data():
    return TestData

@pytest.fixture
def auth_token():
    """Get authentication token for testing."""
    login_data = {
        "email": "test@example.com",
        "password": "testpassword"
    }
    
    response = requests.post(AUTH_URL, json=login_data)
    response.raise_for_status()
    auth_response = response.json()
    token = auth_response["token"]
    user_id = auth_response["user"]["id"]
    return {"token": token, "user_id": user_id}

@pytest.mark.asyncio
async def test_websocket_connection(auth_token):
    """Test WebSocket connection with authentication."""
    logger.info("\nTesting WebSocket connection...")
    try:
        async with websockets.connect(f"{WS_URL}?token={auth_token['token']}", ping_interval=None) as websocket:
            logger.info("WebSocket connected successfully!")
            
            # Send ping
            logger.debug("Sending ping...")
            await websocket.send("ping")
            response = await websocket.recv()
            logger.info(f"Ping response: {response}")
            assert response == "pong", "Expected 'pong' response to ping"
            
            # Keep connection alive for a few seconds to receive notifications
            logger.info("Waiting for notifications (5 seconds)...")
            await asyncio.sleep(5)
            
    except Exception as e:
        logger.error(f"WebSocket test failed: {str(e)}")
        raise

def test_create_notification(auth_token, test_data):
    """Test creating a notification."""
    logger.info("\nTesting create notification...")
    notification_data = {
        "user_id": auth_token["user_id"],
        "notification_type": "test_notification",
        "data": {
            "message": "This is a test notification",
            "timestamp": datetime.now().isoformat()
        }
    }
    
    headers = {"Authorization": f"Bearer {auth_token['token']}"}
    
    response = requests.post(NOTIFICATIONS_URL, json=notification_data, headers=headers)
    response.raise_for_status()
    logger.info(f"Create notification response: {response.status_code}")
    result = response.json()
    logger.info(f"Created notification: {result}")
    
    assert response.status_code == 200, "Expected 200 status code for notification creation"
    assert "id" in result, "Response should contain notification ID"
    assert result["user_id"] == auth_token["user_id"], "Notification should be assigned to correct user"
    
    # Store notification ID in test data
    test_data.notification_id = result["id"]

def test_get_notifications(auth_token, test_data):
    """Test getting notifications."""
    logger.info("\nTesting get notifications...")
    headers = {"Authorization": f"Bearer {auth_token['token']}"}
    
    response = requests.get(NOTIFICATIONS_URL, headers=headers)
    response.raise_for_status()
    logger.info(f"Get notifications response: {response.status_code}")
    notifications = response.json()
    logger.info(f"Found {len(notifications)} notifications:")
    for notification in notifications:
        logger.info(f"- {notification}")
    
    assert response.status_code == 200, "Expected 200 status code for getting notifications"
    assert isinstance(notifications, list), "Response should be a list of notifications"
    assert len(notifications) > 0, "Should have at least one notification"
    
    # Verify the notification we just created is in the list
    assert any(n["id"] == test_data.notification_id for n in notifications), \
        "Recently created notification should be in the list"

def test_mark_as_read(auth_token, test_data):
    """Test marking a notification as read."""
    logger.info("\nTesting mark as read...")
    
    # Use the notification ID from the create test
    notification_id = test_data.notification_id
    assert notification_id is not None, "No notification ID available from create test"
    
    headers = {"Authorization": f"Bearer {auth_token['token']}"}
    
    response = requests.post(f"{NOTIFICATIONS_URL}/{notification_id}/read", headers=headers)
    response.raise_for_status()
    logger.info(f"Mark as read response: {response.status_code}")
    logger.info("Successfully marked notification as read")
    
    assert response.status_code == 200, "Expected 200 status code for marking notification as read"
    
    # Verify the notification is marked as read
    response = requests.get(NOTIFICATIONS_URL, headers=headers)
    notifications = response.json()
    marked_notification = next(n for n in notifications if n["id"] == notification_id)
    assert marked_notification["read"] is True, "Notification should be marked as read"
    assert marked_notification["read_at"] is not None, "read_at timestamp should be set"

@pytest.mark.asyncio
async def test_notification_flow(auth_token, test_data):
    """Test the complete notification flow."""
    # Create a notification
    test_create_notification(auth_token, test_data)
    assert test_data.notification_id is not None, "Notification creation failed"
    
    # Get notifications
    test_get_notifications(auth_token, test_data)
    
    # Mark notification as read
    test_mark_as_read(auth_token, test_data)
    
    # Test WebSocket connection
    await test_websocket_connection(auth_token) 