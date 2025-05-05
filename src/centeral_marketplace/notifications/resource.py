from typing import List, Dict, Any, Optional
from fastapi import APIRouter, WebSocket, Depends, HTTPException, status, Query
from fastapi_injector import Injected
from .manager import manager
from .service import NotificationService
from .core import Notification
from middleware import get_current_user
from centeral_marketplace.users.core import User
from centeral_marketplace.users.service import UserService
from centeral_marketplace.users.auth import decode_token
from core import PyObjectId
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

notifications_router = APIRouter(
    prefix="/notifications",
    tags=["notifications"]
)

_service_lock = asyncio.Lock()
_notification_service = None

async def get_notification_service() -> NotificationService:
    """Dependency to get the notification service."""
    global _notification_service
    
    async with _service_lock:
        if _notification_service is None:
            # In a real app, this would be injected
            from .repository import NotificationRepository
            repository = NotificationRepository()
            await repository.initialize()  # Initialize Redis connection
            _notification_service = NotificationService(repository)
            
        return _notification_service

@notifications_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, 
    token: Optional[str] = None,
    user_id: Optional[str] = None
):
    """WebSocket endpoint for real-time notifications."""
    # Validate authentication
    if not user_id and not token:
        logger.warning("WebSocket connection attempt without authentication")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        # If token is provided, verify it and get user_id
        if token:
            try:
                payload = decode_token(token)
                user_id = payload.get("sub")
                if not user_id:
                    logger.warning("Token provided but no user_id found in payload")
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    return
            except Exception as e:
                logger.error(f"Error decoding token: {e}")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

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

@notifications_router.get("", response_model=List[Dict[str, Any]])
async def get_notifications(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    service: NotificationService = Depends(get_notification_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get notifications for the current user.
    
    Parameters:
    - limit: Maximum number of notifications to return (default: 20)
    - offset: Offset for pagination (default: 0)
    - unread_only: If true, only return unread notifications (default: false)
    """
    try:
        return await service.get_user_notifications(
            str(current_user.id),
            limit=limit,
            offset=offset,
            unread_only=unread_only
        )
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notifications"
        )

@notifications_router.post("/{notification_id}/read", response_model=Dict[str, bool])
async def mark_notification_as_read(
    notification_id: str,
    service: NotificationService = Depends(get_notification_service),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a notification as read.
    
    Parameters:
    - notification_id: ID of the notification to mark as read
    """
    try:
        # First verify the notification belongs to the user
        notifications = await service.get_user_notifications(str(current_user.id))
        if not any(n.get("id") == notification_id for n in notifications):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this notification"
            )
        
        success = await service.mark_as_read(notification_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification with ID {notification_id} not found"
            )
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )

@notifications_router.post("", response_model=Dict[str, Any])
async def create_notification(
    notification: Dict[str, Any],
    service: NotificationService = Depends(get_notification_service),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new notification.
    
    Request body:
    - user_id: ID of the user to notify (must be the current user or an admin)
    - notification_type: Type of notification
    - data: Additional data for the notification
    """
    try:
        user_id = notification.get("user_id")
        notification_type = notification.get("notification_type")
        data = notification.get("data", {})
        
        if not user_id or not notification_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id and notification_type are required"
            )
        
        # Convert user_id to string for comparison
        current_user_id = str(current_user.id)
        target_user_id = str(user_id)
        
        # Only allow creating notifications for self
        if target_user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create notifications for other users"
            )
        
        result = await service.create_notification(
            target_user_id,
            notification_type,
            data
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create notification"
            )
            
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification"
        ) 