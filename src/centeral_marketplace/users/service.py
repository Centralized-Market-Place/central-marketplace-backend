from dataclasses import dataclass
from datetime import datetime, UTC, timedelta
import hashlib
import hmac
import logging
import traceback
from typing import List

from core import PyObjectId
from centeral_marketplace.notifications.core import NotificationType
from centeral_marketplace.notifications.service import NotificationService
from pydantic import EmailStr

from centeral_marketplace.infrastructure.json import Pagination, PaginatedResponse
from config import Config
from fastapi import HTTPException, status, BackgroundTasks
from injector import inject, singleton

from centeral_marketplace.users.repository import UserRepository
from centeral_marketplace.email.repository import EmailVerificationTokenRepository
from centeral_marketplace.users.auth import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from centeral_marketplace.users.core import (
    Role,
    TelegramData,
    TelegramLogin,
    User,
    UserCreate,
    UserProfileUpdate,
    ContactInfo,
)
from centeral_marketplace.email.core import EmailVerificationToken, VerifyEmailResponse, ResendVerificationResponse
from centeral_marketplace.email.service import EmailService
import secrets

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


@singleton
@inject
@dataclass
class UserService:
    user_repository: UserRepository
    notification_service: NotificationService
    config: Config
    email_verification_token_repository: EmailVerificationTokenRepository
    email_service: EmailService

    def find_all(
        self, pagination: Pagination = None, sort_by: str = None, sort_desc: bool = True
    ) -> PaginatedResponse[User]:
        try:
            return self.user_repository.find_all(
                pagination=pagination, sort_by=sort_by, sort_desc=sort_desc
            )
        except Exception as e:
            logger.error(f"Error finding all users: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve users",
            ) from e

    def count_all_by_dict(self, criteria: dict) -> int:
        try:
            return self.user_repository.count_all_by_dict(criteria)
        except Exception as e:
            logger.error(f"Error counting users: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to count users",
            ) from e

    def find_user_by_email(self, email: EmailStr) -> User:
        try:
            user = self.user_repository.find_one_by_dict({"email": email})
            if not user:
                logger.error(f"User with email {email} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with email {email} not found",
                )
            return user
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error finding user by email {email}: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to find user",
            ) from e

    def find_one(self, user_id: PyObjectId) -> User:
        try:
            user = self.user_repository.find_one(user_id)
            if not user:
                logger.error(f"User with ID {user_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found",
                )
            return user
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error finding user {user_id}: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve user",
            ) from e

    def register_user(self, user: UserCreate, background_tasks: BackgroundTasks | None = None) -> User:
        existing_user = self.user_repository.find_one_by_dict({"email": user.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with the current email already exist",
            )
        hashed_password = hash_password(user.password)
        contact_info = ContactInfo(email=user.email)

        now = datetime.now(UTC)
        created_user = User(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            contact_info=contact_info,
            password_hash=hashed_password,
            created_at=now,
        )

        self.notification_service.create_notification(
            user_id=created_user.id,
            content=f"Welcome to the platform {created_user.first_name} {created_user.last_name}",
            notification_type=NotificationType.SYSTEM,
        )

        saved_user = self.user_repository.save(created_user)

        if background_tasks:
            background_tasks.add_task(
                self._send_verification_email, 
                user_id=saved_user.id, 
                email=saved_user.email, 
                first_name=saved_user.first_name
            )
        else:
            self._send_verification_email(
                user_id=saved_user.id, 
                email=saved_user.email, 
                first_name=saved_user.first_name
            )

        return saved_user
        
    def _send_verification_email(self, user_id: PyObjectId, email: str, first_name: str):
        now = datetime.now(UTC)
        token = secrets.token_urlsafe(32)
        expires_at = now + timedelta(hours=24)
        verification_token = EmailVerificationToken(
            token=token,
            user_id=user_id,
            created_at=now,
            expires_at=expires_at
        )
        self.email_verification_token_repository.save_token(verification_token)
        verification_link = f"{self.config.web_app_url}/verify-email?token={token}"
        self.email_service.send_verification_email(email, verification_link, user_name=first_name)
        
    def verify_email(self, token: str) -> VerifyEmailResponse:
        token_obj = self.email_verification_token_repository.get_token(token)
        
        if not token_obj:
            return VerifyEmailResponse(message="Invalid or expired token")
        
        user = self.user_repository.find_one(token_obj.user_id)
        
        if not user:
            return VerifyEmailResponse(message="User not found")
        
        if user.verification_status.email_verified or user.is_verified:
            return VerifyEmailResponse(message="Email already verified")
        
        if token_obj.expires_at:
            expires_at = token_obj.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)
            if expires_at < datetime.now(UTC):
                self.email_verification_token_repository.delete_token(token)
                return VerifyEmailResponse(message="Token expired. Please request a new verification email.")
        
        user.verification_status.email_verified = True
        user.is_verified = True
        self.user_repository.save(user)
        return VerifyEmailResponse(message="Email verified successfully")
        
    def resend_verification(self, email: str, background_tasks: BackgroundTasks | None = None) -> ResendVerificationResponse:
        user = self.user_repository.find_one_by_dict({"email": email})
        
        if not user:
            return ResendVerificationResponse(message="User not found")
            
        if user.verification_status.email_verified or user.is_verified:
            return ResendVerificationResponse(message="Email is already verified")
            
        self.email_verification_token_repository.delete_tokens_for_user(user.id)
        
        if background_tasks:
            background_tasks.add_task(
                self._send_verification_email, 
                user_id=user.id, 
                email=user.email, 
                first_name=user.first_name
            )
        else:
            self._send_verification_email(
                user_id=user.id, 
                email=user.email, 
                first_name=user.first_name
            )
            
        return ResendVerificationResponse(message="Verification email resent")

    def create_admin(self, user: UserCreate) -> User:
        existing_user = self.user_repository.find_one_by_dict({"email": user.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with the current email already exist",
            )
        hashed_password = hash_password(user.password)
        now = datetime.now(UTC)
        created_user = User(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            password_hash=hashed_password,
            role=Role.SUPER_ADMIN,
            is_verified=True,
            created_at=now,
        )
        logger.info(f"Creating admin user: {created_user}")
        return self.user_repository.save(created_user)

    def authenticate_user(self, email: EmailStr, password: str) -> str:
        try:
            user = self.user_repository.find_one_by_dict({"email": email})
            if not user or not verify_password(password, user.password_hash):
                logger.error(f"Authentication failed for email {email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )
            user.last_login = datetime.utcnow()
            self.user_repository.save(user)
            logger.info(f"User {user.id} authenticated successfully")
            return create_access_token({"sub": str(user.id)})
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error authenticating user {email}: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed",
            ) from e

    def validate_token(self, token: str) -> User:
        try:
            payload = decode_token(token)
            user_id = payload.get("sub")
            user = self.user_repository.find_one(user_id)
            if not user:
                logger.error(f"Invalid token - user {user_id} not found")
                raise ValueError("Invalid Token")
            return user
        except Exception as e:
            logger.error(f"Token validation failed: {traceback.format_exc()}")
            raise ValueError("Invalid Token") from e

    def verify_telegram_auth(self, data: TelegramLogin) -> bool:
        received_data = data.model_dump()
        data_check_arr = []

        check_hash = received_data.pop("hash")

        for key, value in sorted(received_data.items()):
            if value is not None:
                data_check_arr.append(f"{key}={value}")

        data_check_string = "\n".join(data_check_arr)

        secret_key = hashlib.sha256(self.config.telegram_bot_token.encode()).digest()

        computed_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(computed_hash, check_hash)

    def login_telegram_user(self, data: TelegramLogin) -> User:
        try:
            user = self.user_repository.find_one_by_dict(
                {"telegram.telegram_id": data.id}
            )

            if not user:
                now = datetime.now(UTC)
                user = User(
                    first_name=data.first_name,
                    last_name=data.last_name,
                    password_hash="",
                    role=Role.USER,
                    created_at=now,
                    telegram=TelegramData(
                        telegram_id=data.id,
                        first_name=data.first_name,
                        last_name=data.last_name,
                        username=data.username,
                        photo_url=data.photo_url,
                    ),
                )
                user.is_verified = True

            else:
                user.telegram = TelegramData(
                    telegram_id=data.id,
                    first_name=data.first_name,
                    last_name=data.last_name,
                    username=data.username,
                    photo_url=data.photo_url,
                )
                user.last_login = datetime.utcnow()

            self.user_repository.save(user)
            return user
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Error while logging in telegram user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error",
            )

    def update_profile(
        self, user_id: PyObjectId, profile_data: UserProfileUpdate
    ) -> User:
        user = self.find_one(user_id)

        for key, value in profile_data.model_dump(exclude_unset=True).items():
            setattr(user, key, value)

        return self.user_repository.save(user)

    def get_profile_completion(self, user_id: PyObjectId) -> dict:
        user = self.find_one(user_id)
        return {
            "is_complete": user.is_profile_complete(),
            "completion_percentage": user.get_completion_percentage(),
            "missing_fields": self._get_missing_fields(user),
        }

    def _get_missing_fields(self, user: User) -> List[str]:
        missing_fields = []
        if not user.first_name:
            missing_fields.append("first_name")
        if not user.last_name:
            missing_fields.append("last_name")
        if not user.contact_info.phone_number:
            missing_fields.append("phone_number")
        if not user.location_info.country:
            missing_fields.append("country")
        if not user.location_info.city:
            missing_fields.append("city")
        return missing_fields

    def request_telegram_email_add(self, user_id: PyObjectId, email: EmailStr, background_tasks: BackgroundTasks | None = None) -> User:
        user = self.find_one(user_id)
        
        if not user.telegram:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not a Telegram user"
            )
            
        if user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an email associated"
            )
            
        existing_user = self.user_repository.find_one_by_dict({"email": email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already in use"
            )
            
        now = datetime.now(UTC)
        token = secrets.token_urlsafe(32)
        expires_at = now + timedelta(hours=24)
        verification_token = EmailVerificationToken(
            token=token,
            user_id=user_id,
            created_at=now,
            expires_at=expires_at,
            metadata={"action": "telegram_email_password_setup", "email": email}
        )
        
        self.email_verification_token_repository.save_token(verification_token)
        verification_link = f"{self.config.web_app_url}/telegram-email-setup?token={token}"
        
        if background_tasks:
            background_tasks.add_task(
                self.email_service.send_verification_email,
                to_email=email,
                verification_link=verification_link,
                user_name=user.first_name
            )
        else:
            self.email_service.send_verification_email(
                to_email=email,
                verification_link=verification_link,
                user_name=user.first_name
            )
            
        return user

    def complete_telegram_email_password_setup(self, token: str, password: str) -> User:
        token_obj = self.email_verification_token_repository.get_token(token)
        
        if not token_obj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'token object not found for token: {token}'
            )
            
        if not token_obj.metadata or token_obj.metadata.get("action") != "telegram_email_password_setup":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="token is not valid for password set"
            )
            
        user = self.user_repository.find_one(token_obj.user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user not associated with the given token"

            )
            
        if token_obj.expires_at:
            expires_at = token_obj.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)
            if expires_at < datetime.now(UTC):
                self.email_verification_token_repository.delete_token(token)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="token has expired"
                )
        
        email = token_obj.metadata.get("email")
        user.email = email
        user.password_hash = hash_password(password)
        user.verification_status.email_verified = True
        user.is_verified = True
        
        self.user_repository.save(user)
        self.email_verification_token_repository.delete_token(token)

        return user