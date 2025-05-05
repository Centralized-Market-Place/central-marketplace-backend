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

router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["notifications"]
)

def get_notification_service() -> NotificationService:
    """Dependency to get the notification service."""
    # In a real app, this would be injected
    from .repository import NotificationRepository
    repository = NotificationRepository()
    return NotificationService(repository)

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: str = None,
    token: str = None
):
    """WebSocket endpoint for real-time notifications."""
    if not user_id and not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    final_user_id = user_id
    
    try:
        await manager.connect(websocket, final_user_id)
        
        while True:
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
            except Exception:
                manager.disconnect(final_user_id)
                break
    except Exception:
        manager.disconnect(final_user_id)

@router.get("", response_model=List[Dict[str, Any]])
async def get_notifications(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    service: NotificationService = Depends(get_notification_service)
):
    """
    Get notifications for a user.
    
    Parameters:
    - user_id: ID of the user
    - limit: Maximum number of notifications to return (default: 20)
    - offset: Offset for pagination (default: 0)
    - unread_only: If true, only return unread notifications (default: false)
    """
    return await service.get_user_notifications(
        user_id,
        limit=limit,
        offset=offset,
        unread_only=unread_only
    )

@router.post("/{notification_id}/read", response_model=Dict[str, bool])
async def mark_notification_as_read(
    notification_id: str,
    service: NotificationService = Depends(get_notification_service)
):
    """
    Mark a notification as read.
    
    Parameters:
    - notification_id: ID of the notification to mark as read
    """
    success = await service.mark_as_read(notification_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {notification_id} not found"
        )
    return {"success": True}

@router.post("", response_model=Dict[str, Any])
async def create_notification(
    notification: Dict[str, Any],
    service: NotificationService = Depends(get_notification_service)
):
    """
    Create a new notification.
    
    Request body:
    - user_id: ID of the user to notify
    - notification_type: Type of notification
    - data: Additional data for the notification
    """
    user_id = notification.get("user_id")
    notification_type = notification.get("notification_type")
    data = notification.get("data", {})
    
    if not user_id or not notification_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id and notification_type are required"
        )
    
    result = await service.create_notification(
        user_id,
        notification_type,
        data
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification"
        )
        
    return result 