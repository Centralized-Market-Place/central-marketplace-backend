import pytest
import asyncio
import json
import uuid
import logging
from fastapi.testclient import TestClient
from bson import ObjectId

from centeral_marketplace.users.auth import create_access_token
from centeral_marketplace.users.core import User, Role
from centeral_marketplace.comments.core import CommentCreate
from centeral_marketplace.products.core import Product
from centeral_marketplace.notifications.core import Notification

from tests.core.given import given, when
from tests.core.modules import create_test_client, prepare_api_server, prepare_injector
from tests.steps.database import database_is_clean, database_repo_is_ready
from tests.steps.users import there_is_a_user
from tests.steps.notifications import notification_repository_is_ready

logger = logging.getLogger(__name__)

class WebSocketClient:
    """Helper class to manage WebSocket connections in tests."""
    
    def __init__(self, client: TestClient, url: str):
        self.client = client
        self.url = url
        self.websocket = None
        self.messages = []
        
    def __enter__(self):
        self.websocket = self.client.websocket_connect(self.url)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.websocket:
            self.websocket.close()
            
    def receive_json(self, timeout=1.0):
        """Receive a message with timeout."""
        start_time = asyncio.get_event_loop().time()
        
        # Keep trying until timeout
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                message = self.websocket.receive_json()
                self.messages.append(message)
                return message
            except Exception:
                # Sleep briefly before trying again
                asyncio.sleep(0.1)
                
        return None
        
    def get_notifications_by_type(self, notification_type):
        """Get notifications of a specific type from received messages."""
        return [msg for msg in self.messages if msg.get('notification_type') == notification_type]

@pytest.mark.e2e
def test_user_receives_notification_when_comment_added():
    """
    End-to-end test: Verify a user receives a notification when someone 
    comments on their product.
    """
    # Generate unique test IDs
    test_id = str(uuid.uuid4())[:8]
    product_owner_email = f"owner_{test_id}@example.com"
    commenter_email = f"commenter_{test_id}@example.com"
    
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            notification_repository_is_ready(),
            # Create a product owner
            there_is_a_user(name="Product Owner", email=product_owner_email, password="password"),
            # Create a commenter 
            there_is_a_user(name="Commenter", email=commenter_email, password="password"),
        ]
    ) as context:
        client: TestClient = context.client
        
        # Get user IDs and tokens
        owner = context.user  # First user created is product owner
        owner_id = str(owner.id)
        owner_token = create_access_token({"sub": owner_id})
        
        # Login as commenter
        login_response = client.post(
            "/api/v1/users/login",
            json={
                "email": commenter_email,
                "password": "password"
            }
        )
        assert login_response.status_code == 200
        commenter_data = login_response.json()
        commenter_token = commenter_data["token"]
        commenter_id = commenter_data["user"]["id"]
        
        # Create a test product as the owner
        product_data = {
            "name": f"Test Product {test_id}",
            "description": "Product for testing notifications",
            "price": 99.99,
            "channel_id": 12345
        }
        
        product_response = client.post(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {owner_token}"},
            json=product_data
        )
        
        # Check product creation
        assert product_response.status_code == 200
        product = product_response.json()
        product_id = product["id"]
        
        # Connect to WebSocket as product owner to receive notifications
        websocket_url = f"/api/v1/notifications/ws?user_id={owner_id}"
        
        with WebSocketClient(client, websocket_url) as ws:
            # Create a comment on the product as commenter
            comment_data = {
                "text": f"Test comment from e2e test {test_id}"
            }
            
            comment_response = client.post(
                f"/api/v1/products/{product_id}/comments",
                headers={"Authorization": f"Bearer {commenter_token}"},
                json=comment_data
            )
            
            # Check comment creation
            assert comment_response.status_code == 200
            comment = comment_response.json()
            comment_id = comment["id"]
            
            # Wait for and verify notification
            notification = ws.receive_json(timeout=5.0)  # Increased timeout for e2e test
            
            # Verify notification was received
            assert notification is not None, "No notification received"
            assert notification["user_id"] == owner_id
            assert notification["notification_type"] == "product_comment" or notification["notification_type"] == "comment"
            assert notification["data"]["product_id"] == product_id
            assert notification["data"]["comment_id"] == comment_id
            
            # Verify notification is in database
            notifications_response = client.get(
                "/api/v1/notifications",
                headers={"Authorization": f"Bearer {owner_token}"}
            )
            
            assert notifications_response.status_code == 200
            notifications = notifications_response.json()
            
            # Find the notification for this comment
            matching_notifications = [
                n for n in notifications 
                if n["data"].get("comment_id") == comment_id
            ]
            
            assert len(matching_notifications) > 0, "Notification not found in database"

@pytest.mark.e2e
def test_comment_author_receives_notification_when_reply_added():
    """
    End-to-end test: Verify a comment author receives a notification when 
    someone replies to their comment.
    """
    # Generate unique test IDs
    test_id = str(uuid.uuid4())[:8]
    product_owner_email = f"owner_{test_id}@example.com"
    commenter_email = f"commenter_{test_id}@example.com"
    replier_email = f"replier_{test_id}@example.com"
    
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            notification_repository_is_ready(),
            # Create users
            there_is_a_user(name="Product Owner", email=product_owner_email, password="password"),
            there_is_a_user(name="Commenter", email=commenter_email, password="password"),
            there_is_a_user(name="Replier", email=replier_email, password="password"),
        ]
    ) as context:
        client: TestClient = context.client
        
        # Setup users and tokens
        product_owner = context.users[0] if hasattr(context, 'users') else context.user
        product_owner_id = str(product_owner.id)
        product_owner_token = create_access_token({"sub": product_owner_id})
        
        # Login as commenter
        login_response = client.post(
            "/api/v1/users/login",
            json={
                "email": commenter_email,
                "password": "password"
            }
        )
        assert login_response.status_code == 200
        commenter_data = login_response.json()
        commenter_token = commenter_data["token"]
        commenter_id = commenter_data["user"]["id"]
        
        # Login as replier
        login_response = client.post(
            "/api/v1/users/login",
            json={
                "email": replier_email,
                "password": "password"
            }
        )
        assert login_response.status_code == 200
        replier_data = login_response.json()
        replier_token = replier_data["token"]
        replier_id = replier_data["user"]["id"]
        
        # Create a test product as the owner
        product_data = {
            "name": f"Test Product {test_id}",
            "description": "Product for testing notifications",
            "price": 99.99,
            "channel_id": 12345
        }
        
        product_response = client.post(
            "/api/v1/products",
            headers={"Authorization": f"Bearer {product_owner_token}"},
            json=product_data
        )
        
        # Check product creation
        assert product_response.status_code == 200
        product = product_response.json()
        product_id = product["id"]
        
        # Create a comment as commenter
        comment_data = {
            "text": f"Original comment from e2e test {test_id}"
        }
        
        comment_response = client.post(
            f"/api/v1/products/{product_id}/comments",
            headers={"Authorization": f"Bearer {commenter_token}"},
            json=comment_data
        )
        
        # Check comment creation
        assert comment_response.status_code == 200
        comment = comment_response.json()
        comment_id = comment["id"]
        
        # Connect to WebSocket as commenter to receive reply notifications
        websocket_url = f"/api/v1/notifications/ws?user_id={commenter_id}"
        
        with WebSocketClient(client, websocket_url) as ws:
            # Create a reply to the comment as replier
            reply_data = {
                "text": f"Reply to comment from e2e test {test_id}"
            }
            
            reply_response = client.post(
                f"/api/v1/products/{product_id}/comments/{comment_id}",
                headers={"Authorization": f"Bearer {replier_token}"},
                json=reply_data
            )
            
            # Check reply creation 
            assert reply_response.status_code == 200
            reply = reply_response.json()
            reply_id = reply["id"]
            
            # Wait for and verify notification
            notification = ws.receive_json(timeout=5.0)
            
            # Verify notification was received
            assert notification is not None, "No notification received"
            assert notification["user_id"] == commenter_id
            assert notification["notification_type"] == "comment_reply" or notification["notification_type"] == "reply"
            assert notification["data"]["product_id"] == product_id
            assert notification["data"]["comment_id"] == comment_id
            assert notification["data"]["reply_id"] == reply_id 