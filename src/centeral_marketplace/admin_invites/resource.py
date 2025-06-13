from typing import Annotated, Optional
from fastapi import APIRouter, Depends, BackgroundTasks, Query, status
from fastapi_injector import Injected

from centeral_marketplace.admin_invites.service import AdminInvitationService
from centeral_marketplace.infrastructure.json import Pagination, PaginatedResponse
from centeral_marketplace.admin_invites.core import (
    AdminInvitation,
    AdminInvitationCreate,
    AdminInvitationAccept,
    InvitationStatus,
)
from centeral_marketplace.users.core import Role, User, UserPublic
from middleware import require_role
from core import PyObjectId


admin_invites_router = APIRouter(
    prefix="/admin-invites",
    tags=["admin-invites"],
)


@admin_invites_router.post(
    "/invite", response_model=AdminInvitation, status_code=status.HTTP_201_CREATED
)
async def invite_admin_user(
    invitation_data: AdminInvitationCreate,
    current_user: Annotated[User, Depends(require_role([Role.SUPER_ADMIN.value]))],
    background_tasks: BackgroundTasks,
    admin_invitation_service: AdminInvitationService = Injected(AdminInvitationService),
):
    return admin_invitation_service.invite_admin_user(
        current_user, invitation_data, background_tasks=background_tasks
    )


@admin_invites_router.get("/", response_model=PaginatedResponse[AdminInvitation])
async def get_invitations(
    _: Annotated[User, Depends(require_role([Role.SUPER_ADMIN.value]))],
    page: int = 1,
    page_size: int = 10,
    status: Optional[InvitationStatus] = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_desc: bool = Query(default=True),
    admin_invitation_service: AdminInvitationService = Injected(AdminInvitationService),
):
    pagination = Pagination(page=page, size=page_size)
    return admin_invitation_service.get_all_invitations(
        pagination=pagination, status=status, sort_by=sort_by, sort_desc=sort_desc
    )


@admin_invites_router.post("/{invitation_id}/cancel", response_model=AdminInvitation)
async def cancel_admin_invitation(
    invitation_id: PyObjectId,
    current_user: Annotated[User, Depends(require_role([Role.SUPER_ADMIN.value]))],
    admin_invitation_service: AdminInvitationService = Injected(AdminInvitationService),
):
    return admin_invitation_service.cancel_invitation(invitation_id)


@admin_invites_router.post(
    "/accept", response_model=UserPublic, status_code=status.HTTP_201_CREATED
)
async def accept_admin_invitation(
    invitation_data: AdminInvitationAccept,
    admin_invitation_service: AdminInvitationService = Injected(AdminInvitationService),
):
    return admin_invitation_service.accept_admin_invitation(invitation_data)


@admin_invites_router.get("/token/{token}", response_model=AdminInvitation)
async def get_invitation_by_token(
    token: str,
    admin_invitation_service: AdminInvitationService = Injected(AdminInvitationService),
):
    return admin_invitation_service.get_invitation_by_token(token)
