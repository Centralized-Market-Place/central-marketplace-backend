import pytest
import json
import logging
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
from starlette.websockets import WebSocket
from src.centeral_marketplace.notifications.manager import WebSocketManager, manager

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

@pytest.fixture
def test_client():
    """Create a test client."""
    from src.centeral_marketplace.main import app
    return TestClient(app)

def test_websocket_connection_rejection(test_client):
    """Test that WebSocket connection is rejected without auth."""
    try:
        with test_client.websocket_connect("/api/v1/notifications/ws") as websocket:
            pytest.fail("WebSocket connection should be rejected")
    except WebSocketDisconnect as e:
        logger.debug(f"WebSocket disconnected as expected: {e}")
        pass  # This is expected

def test_websocket_connection_success(test_client):
    """Test that WebSocket connection can be established with auth."""
    user_id = "test_user"
    websocket_url = f"/api/v1/notifications/ws?user_id={user_id}"
    
    with test_client.websocket_connect(websocket_url) as websocket:
        assert websocket is not None
        
        # Send a ping message and expect a pong response
        websocket.send_text("ping")
        response = websocket.receive_text()
        assert response == "pong"

def test_websocket_basic_messaging(test_client):
    """Test basic message exchange via WebSocket."""
    user_id = "test_user"
    websocket_url = f"/api/v1/notifications/ws?user_id={user_id}"
    
    with test_client.websocket_connect(websocket_url) as websocket:
        # Test ping-pong
        websocket.send_text("ping")
        response = websocket.receive_text()
        assert response == "pong"
        
        # Test sending a custom message
        websocket.send_text(json.dumps({"type": "test", "content": "Test message"}))
        
        # We don't expect a response for a custom message,
        # but we need to check that the connection remains open
        try:
            # Try to send another ping
            websocket.send_text("ping")
            response = websocket.receive_text()
            assert response == "pong"
        except Exception as e:
            pytest.fail(f"Connection should remain open after sending custom message: {e}")

@pytest.mark.parametrize("auth_method", [
    "query_param", 
    "missing_auth"
])
def test_websocket_authentication(test_client, auth_method):
    """Test WebSocket authentication with different methods."""
    if auth_method == "query_param":
        user_id = "test_user"
        websocket_url = f"/api/v1/notifications/ws?user_id={user_id}"
        
        with test_client.websocket_connect(websocket_url) as websocket:
            # Send a ping to verify connection
            websocket.send_text("ping")
            response = websocket.receive_text()
            assert response == "pong"
    
    elif auth_method == "missing_auth":
        websocket_url = "/api/v1/notifications/ws"
        
        try:
            with test_client.websocket_connect(websocket_url) as websocket:
                pytest.fail("Connection should be rejected without authentication")
        except WebSocketDisconnect:
            # This is expected
            pass 