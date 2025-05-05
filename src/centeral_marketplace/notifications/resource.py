from typing import List, Optional
from fastapi import APIRouter, WebSocket, Depends, HTTPException, status, Query
from fastapi_injector import Injected
from .manager import manager
from .service import NotificationService
from .core import Notification
from middleware import get_current_user
from centeral_marketplace.users.core import User
from centeral_marketplace.users.service import UserService
from centeral_marketplace.users.auth import decode_token

notifications_router = APIRouter(
    prefix="/notifications",
    tags=["notifications"]
)

@notifications_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, 
    token: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    user_service: UserService = Injected(UserService)
):
    # Try to authenticate with token
    authenticated_user_id = None
    if token:
        try:
            user = user_service.validate_token(token)
            authenticated_user_id = str(user.id)
        except Exception as e:
            print(f"Authentication error: {e}")
    
    # Fallback to user_id query param for testing
    final_user_id = authenticated_user_id or user_id
    if not final_user_id:
        await websocket.close(code=1008)  # Policy violation
        return
    
    await manager.connect(websocket, final_user_id)
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except Exception:
        manager.disconnect(final_user_id)

@notifications_router.get("/", response_model=List[Notification])
async def get_notifications(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Injected(NotificationService),
    limit: int = 50
):
    return await notification_service.get_user_notifications(str(current_user.id), limit)

@notifications_router.post("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Injected(NotificationService)
):
    notification = await notification_service.mark_as_read(notification_id, str(current_user.id))
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return notification 