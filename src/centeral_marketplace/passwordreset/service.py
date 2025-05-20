from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
import secrets
from fastapi import HTTPException, status
from .core import PasswordResetToken
from centeral_marketplace.users.repository import UserRepository
from centeral_marketplace.email.service import EmailService
from .repository import PasswordResetRepository
from injector import inject, singleton

@inject
@singleton
@dataclass
class PasswordResetService:
    password_reset_repository: PasswordResetRepository
    user_repository: UserRepository
    email_service: EmailService
    def initiate_password_reset(self, email: str):
        user = self.user_repository.find_one_by_dict({"email": email})
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(hours=1)
        reset_token = PasswordResetToken(
            token=token,
            user_id=user.id,
            created_at=datetime.now(UTC),
            expires_at=expires_at
        )
        self.password_reset_repository.save_token(reset_token)
        reset_link = f"https://centeral-marketplace-webapp.vercel.app/reset-password?token={token}"
        self.email_service.send_password_reset_email(user.email, reset_link, user_name=user.first_name)
        return {"message": "Password reset email sent"}

    def confirm_password_reset(self, token: str, new_password: str):
        reset_token = self.password_reset_repository.get_token(token)
        if not reset_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
        expires_at = reset_token.expires_at
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at and expires_at < datetime.now(UTC):
            self.password_reset_repository.delete_token(token)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired")
        user = self.user_repository.find_one(reset_token.user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        from centeral_marketplace.users.auth import hash_password
        user.password_hash = hash_password(new_password)
        self.user_repository.save(user)
        self.password_reset_repository.delete_token(token)
        return {"message": "Password has been reset successfully"} 