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
            
            # Keep connection alive for a few seconds to receive notifications
            logger.info("Waiting for notifications (5 seconds)...")
            await asyncio.sleep(5)
            
    except Exception as e:
        logger.error(f"WebSocket test failed: {str(e)}")
        raise

def test_create_notification(auth_token):
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
    return result.get("id")

def test_get_notifications(auth_token):
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
    return notifications

def test_mark_as_read(auth_token):
    """Test marking a notification as read."""
    logger.info("\nTesting mark as read...")
    
    # First create a notification
    notification_id = test_create_notification(auth_token)
    assert notification_id is not None, "Failed to create notification"
    
    headers = {"Authorization": f"Bearer {auth_token['token']}"}
    
    response = requests.post(f"{NOTIFICATIONS_URL}/{notification_id}/read", headers=headers)
    response.raise_for_status()
    logger.info(f"Mark as read response: {response.status_code}")
    logger.info("Successfully marked notification as read")

@pytest.mark.asyncio
async def test_notification_flow(auth_token):
    """Test the complete notification flow."""
    # Create a notification
    notification_id = test_create_notification(auth_token)
    assert notification_id is not None, "Failed to create notification"
    
    # Get notifications
    notifications = test_get_notifications(auth_token)
    assert len(notifications) > 0, "No notifications found"
    assert any(n.get("id") == notification_id for n in notifications), "Created notification not found"
    
    # Mark notification as read
    test_mark_as_read(auth_token)
    
    # Test WebSocket connection
    await test_websocket_connection(auth_token) 