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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from src.centeral_marketplace.notifications.resource import notifications_router
app.include_router(notifications_router, prefix="/api/v1")

@app.get("/api/v1/health_check")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "websocket_connections": len(manager.active_connections)} 