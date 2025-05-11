import requests
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8443/api/v1"
REGISTER_URL = f"{BASE_URL}/users/register"

def create_test_user():
    """Create a test user for notification testing."""
    user_data = {
        "email": "test@example.com",
        "password": "testpassword",
        "name": "Test User"
    }
    
    try:
        response = requests.post(REGISTER_URL, json=user_data)
        response.raise_for_status()
        logger.info("Test user created successfully!")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to create test user: {str(e)}")
        if hasattr(e.response, 'text'):
            logger.error(f"Response: {e.response.text}")
        raise

if __name__ == "__main__":
    create_test_user() 