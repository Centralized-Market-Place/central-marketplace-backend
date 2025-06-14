from dataclasses import dataclass
from datetime import datetime, UTC, timedelta
import logging
import traceback
import secrets

from fastapi import HTTPException, status, BackgroundTasks
from injector import inject, singleton

from centeral_marketplace.infrastructure.json import Pagination, PaginatedResponse
from centeral_marketplace.admin_invites.core import (
    AdminInvitation,
    AdminInvitationCreate,
    AdminInvitationAccept,
    InvitationStatus,
)
from centeral_marketplace.admin_invites.repository import AdminInvitationRepository
from centeral_marketplace.users.core import Role, User, ContactInfo
from centeral_marketplace.users.repository import UserRepository
from centeral_marketplace.users.auth import hash_password
from centeral_marketplace.email.service import EmailService
from config import Config
from core import PyObjectId

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


@singleton
@inject
@dataclass
class AdminInvitationService:
    admin_invitation_repository: AdminInvitationRepository
    user_repository: UserRepository
    email_service: EmailService
    config: Config

    def invite_admin_user(
        self,
        current_user: User,
        invitation_data: AdminInvitationCreate,
        background_tasks: BackgroundTasks,
    ) -> AdminInvitation:
        try:
            existing_user = self.user_repository.find_one_by_dict(
                {"email": invitation_data.email}
            )
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email already exists",
                )

            existing_invitation = self.admin_invitation_repository.find_one_by_dict(
                {"email": invitation_data.email, "status": InvitationStatus.PENDING}
            )
            if existing_invitation:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="There is already a pending invitation for this email",
                )

            if invitation_data.role not in [Role.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Can only invite ADMIN role",
                )

            now = datetime.now(UTC)
            token = secrets.token_urlsafe(32)
            expires_at = now + timedelta(hours=48)

            invitation = AdminInvitation(
                email=invitation_data.email,
                invited_by=current_user.id,
                role=invitation_data.role,
                token=token,
                expires_at=expires_at,
                invited_by_name=f"{current_user.first_name} {current_user.last_name or ''}".strip(),
                created_at=now,
            )

            saved_invitation = self.admin_invitation_repository.save(invitation)

            invitation_link = (
                f"{self.config.web_app_url}/accept-invitation/{token}"
            )

            background_tasks.add_task(
                self.email_service.send_admin_invitation_email,
                to_email=invitation_data.email,
                invitation_link=invitation_link,
                role=invitation_data.role.value,
                invited_by_name=invitation.invited_by_name,
                expires_at=expires_at,
            )

            logger.info(
                f"Admin invitation sent to {invitation_data.email} by {current_user.id}"
            )
            return saved_invitation

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error inviting admin user: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to send admin invitation",
            ) from e

    def get_all_invitations(
        self,
        pagination: Pagination | None = None,
        status: InvitationStatus | None = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> PaginatedResponse[AdminInvitation]:
        try:
            criteria = {}
            if status:
                criteria["status"] = status
            return self.admin_invitation_repository.find_all_by_dict(
                criteria=criteria,
                pagination=pagination,
                sort_by=sort_by,
                sort_desc=sort_desc,
            )
        except Exception as e:
            logger.error(f"Error getting all invitations: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve invitations",
            ) from e

    def cancel_invitation(self, invitation_id: PyObjectId) -> AdminInvitation:
        try:
            invitation = self.admin_invitation_repository.find_one(invitation_id)
            if not invitation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Invitation not found",
                )

            if invitation.status != InvitationStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only pending invitations can be cancelled",
                )

            invitation.status = InvitationStatus.CANCELLED
            invitation.updated_at = datetime.now(UTC)

            updated_invitation = self.admin_invitation_repository.save(invitation)
            logger.info(f"Admin invitation {invitation_id} cancelled")
            return updated_invitation

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error cancelling invitation {invitation_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to cancel invitation",
            ) from e
        
    def resend_invitation(self, invitation_id: PyObjectId, background_tasks: BackgroundTasks) -> AdminInvitation:
        try:
            invitation = self.admin_invitation_repository.find_one(invitation_id)
            if not invitation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Invitation not found",
                )
            
            if invitation.status == InvitationStatus.ACCEPTED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invitation already accepted",
                )
            
            now = datetime.now(UTC)
            token = secrets.token_urlsafe(32)
            expires_at = now + timedelta(hours=48)

            invitation.token = token
            invitation.expires_at = expires_at
            invitation.updated_at = now
            invitation.status = InvitationStatus.PENDING

            invitation_link = (
                f"{self.config.web_app_url}/accept-invitation/{token}"
            )

            updated_invitation = self.admin_invitation_repository.save(invitation)

            background_tasks.add_task(
                self.email_service.send_admin_invitation_email,
                to_email=updated_invitation.email,
                invitation_link=invitation_link,
                role=updated_invitation.role.value,
                invited_by_name=updated_invitation.invited_by_name,
                expires_at=expires_at,
            )


            
            logger.info(f"Admin invitation {invitation_id} resent")
            return updated_invitation

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error resending invitation {invitation_id}: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to resend invitation",
            ) from e

    def accept_admin_invitation(self, invitation_data: AdminInvitationAccept) -> User:
        try:
            invitation = self.admin_invitation_repository.find_one_by_dict(
                {"token": invitation_data.token, "status": InvitationStatus.PENDING}
            )

            if not invitation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Invalid or expired invitation token",
                )

            if invitation.expires_at.astimezone(UTC) < datetime.now(UTC):
                invitation.status = InvitationStatus.EXPIRED
                self.admin_invitation_repository.save(invitation)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invitation has expired",
                )

            existing_user = self.user_repository.find_one_by_dict(
                {"email": invitation.email}
            )
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User with this email already exists",
                )

            now = datetime.now(UTC)
            hashed_password = hash_password(invitation_data.password)
            contact_info = ContactInfo(email=invitation.email)

            new_user = User(
                first_name=invitation_data.first_name,
                last_name=invitation_data.last_name,
                email=invitation.email,
                contact_info=contact_info,
                password_hash=hashed_password,
                role=invitation.role,
                is_verified=True,
                created_at=now,
            )
            new_user.verification_status.email_verified = True

            saved_user = self.user_repository.save(new_user)

            invitation.status = InvitationStatus.ACCEPTED
            invitation.accepted_at = now
            self.admin_invitation_repository.save(invitation)

            logger.info(f"Admin invitation accepted for {invitation.email}")
            return saved_user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error accepting admin invitation: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to accept invitation",
            ) from e

    def get_invitation_by_token(self, token: str) -> AdminInvitation:
        try:
            invitation = self.admin_invitation_repository.find_one_by_dict(
                {"token": token}
            )
            if not invitation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Invitation not found",
                )
            return invitation
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting invitation by token: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve invitation",
            ) from e
