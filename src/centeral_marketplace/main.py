from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from injector import Injector, inject
from src.centeral_marketplace.notifications.repository import NotificationRepository
from src.centeral_marketplace.notifications.service import NotificationService
from src.centeral_marketplace.notifications.manager import manager
import logging
import asyncio
import json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Initialize the manager at module level for testing
async def initialize_manager():
    if not getattr(manager, '_initialized', False):
        try:
            logger.info("Initializing WebSocket manager (module level)")
            await manager.initialize()
            logger.info("WebSocket manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket manager: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        logger.info("Starting application, initializing WebSocket manager")
        await manager.initialize()
        logger.info("WebSocket manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize WebSocket manager: {e}")
    
    yield
    
    # Shutdown
    try:
        logger.info("Shutting down application, closing WebSocket manager")
        await manager.close()
        logger.info("WebSocket manager closed successfully")
    except Exception as e:
        logger.error(f"Error during WebSocket manager shutdown: {e}")

app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency injection
injector = Injector()

@inject
def get_notification_repository() -> NotificationRepository:
    return injector.get(NotificationRepository)

@inject
def get_notification_service(
    repository: NotificationRepository = Depends(get_notification_repository)
) -> NotificationService:
    return NotificationService(repository)

@app.websocket("/api/v1/notifications/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = None,
    token: str = None
):
    """WebSocket endpoint for real-time notifications"""
    # Validate authentication
    if not user_id and not token:
        logger.warning("WebSocket connection attempt without authentication")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Ensure manager is initialized (for testing)
    await initialize_manager()

    try:
        # Connect to WebSocket manager
        await manager.connect(websocket, user_id)
        logger.info(f"WebSocket connection established for user {user_id}")
        
        # Keep connection open and handle messages
        while True:
            try:
                # Receive and process messages
                message = await websocket.receive_text()
                
                # Handle ping/pong for connection keepalive
                if message == "ping":
                    await websocket.send_text("pong")
                    logger.debug(f"Received ping from user {user_id}, sent pong")
                elif message == "pong":
                    logger.debug(f"Received pong from user {user_id}")
                else:
                    # Handle other message types if needed
                    try:
                        data = json.loads(message)
                        logger.debug(f"Received message from user {user_id}: {data}")
                    except json.JSONDecodeError:
                        logger.warning(f"Received invalid JSON from user {user_id}: {message}")
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for user {user_id}")
                manager.disconnect(user_id)
                break
            except Exception as e:
                logger.error(f"Error in WebSocket connection for user {user_id}: {e}")
                manager.disconnect(user_id)
                break
                
    except Exception as e:
        logger.error(f"Error setting up WebSocket connection for user {user_id}: {e}")
        manager.disconnect(user_id)
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except Exception:
            pass  # Already closed

@app.get("/api/v1/health_check")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "websocket_connections": len(manager.active_connections)} 