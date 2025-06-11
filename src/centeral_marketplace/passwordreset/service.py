from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
import logging
import secrets
import traceback
from config import Config
from fastapi import BackgroundTasks, HTTPException, status
from typing import Optional
from .core import PasswordResetToken
from centeral_marketplace.users.repository import UserRepository
from centeral_marketplace.email.service import EmailService
from .repository import PasswordResetRepository
from centeral_marketplace.users.auth import hash_password
from injector import inject, singleton

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

@inject
@singleton
@dataclass
class PasswordResetService:
    password_reset_repository: PasswordResetRepository
    user_repository: UserRepository
    email_service: EmailService
    config: Config

    def initiate_password_reset(self, email: str, background_tasks: Optional[BackgroundTasks] = None):
        try:
            user = self.user_repository.find_one_by_dict({"email": email})
            if not user:
                logger.error(f"Password reset requested for non-existent email: {email}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail="User with this email not found"
                )
            
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now(UTC) + timedelta(hours=1)
            
            reset_token = PasswordResetToken(
                token=token,
                user_id=user.id,
                created_at=datetime.now(UTC),
                expires_at=expires_at
            )
            self.password_reset_repository.save_token(reset_token)
            
            reset_link = f"{self.config.web_app_url}/reset-password?token={token}"
            
            if background_tasks:
                self.email_service.send_password_reset_email(
                    user.email, 
                    reset_link, 
                    user_name=user.first_name, 
                    background_tasks=background_tasks
                )
            else:
                self.email_service.send_password_reset_email(
                    user.email, 
                    reset_link, 
                    user_name=user.first_name
                )
            
            logger.info(f"Password reset email sent to {email}")
            return {"message": "Password reset email sent"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error initiating password reset for {email}: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to initiate password reset",
            ) from e

    def confirm_password_reset(self, token: str, new_password: str):
        try:
            reset_token = self.password_reset_repository.get_token(token)
            if not reset_token:
                logger.error(f"Invalid or expired token used for password reset: {token}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Invalid or expired token"
                )
        
            expires_at = reset_token.expires_at
            if expires_at and expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)
            if expires_at and expires_at < datetime.now(UTC):
                self.password_reset_repository.delete_token(token)
                logger.error(f"Expired token used for password reset: {token}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Token expired"
                )
            
            user = self.user_repository.find_one(reset_token.user_id)
            if not user:
                logger.error(f"User not found for password reset token: {reset_token.user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail="User not found"
                )
            
            user.password_hash = hash_password(new_password)
            self.user_repository.save(user)
            
            self.password_reset_repository.delete_token(token)
            
            logger.info(f"Password reset completed for user {user.id}")
            return {"message": "Password has been reset successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error confirming password reset for token {token}: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to reset password",
            ) from e 