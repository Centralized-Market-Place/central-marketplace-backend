from typing import Optional, Annotated
from fastapi import APIRouter, Depends, Query, status
from fastapi_injector import Injected

from centeral_marketplace.infrastructure.json import PaginatedResponse, Pagination
from centeral_marketplace.notifications.service import NotificationService
from centeral_marketplace.notifications.core import Notification
from middleware import get_current_user
from centeral_marketplace.users.core import User
from core import PyObjectId

import logging

logger = logging.getLogger(__name__)

notifications_router = APIRouter(prefix="/notifications", tags=["notifications"])


@notifications_router.get("", response_model=PaginatedResponse[Notification])
async def list_notifications(
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    read: Optional[bool] = Query(
        None, description="Filter by read status (True/False/None for all)"
    ),
    service: NotificationService = Injected(NotificationService),
):
    pagination = Pagination(page=page, size=page_size)
    result = service.get_user_notifications(
        user_id=current_user.id, pagination=pagination, read_filter=read
    )

    return result


@notifications_router.post("/{notification_id}/read", response_model=Notification)
async def mark_notification_as_read(
    notification_id: PyObjectId,
    current_user: Annotated[User, Depends(get_current_user)],
    service: NotificationService = Injected(NotificationService),
):
    return service.mark_as_read(notification_id, current_user.id)


@notifications_router.delete(
    "/{notification_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_notification(
    notification_id: PyObjectId,
    current_user: Annotated[User, Depends(get_current_user)],
    service: NotificationService = Injected(NotificationService),
):
    service.delete_notification(
        notification_id=notification_id, user_id=current_user.id
    )


@notifications_router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_notifications(
    current_user: Annotated[User, Depends(get_current_user)],
    service: NotificationService = Injected(NotificationService),
):
    service.delete_all_for_user(user_id=current_user.id)
