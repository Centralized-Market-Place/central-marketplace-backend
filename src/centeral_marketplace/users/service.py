from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import logging
import time
from typing import Optional, List

from core import PyObjectId
from centeral_marketplace.notifications.core import NotificationType
from centeral_marketplace.notifications.service import NotificationService
from pydantic import EmailStr

from centeral_marketplace.infrastructure.json import Pagination, PaginatedResponse
from config import Config
from fastapi import HTTPException, status
from injector import inject, singleton

from centeral_marketplace.users.repository import UserRepository
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
    PersonalInfo,
    ContactInfo,
    LocationInfo,
    CommunicationPreferences,
    PrivacySettings,
)

logger = logging.getLogger(__name__)


@singleton
@inject
@dataclass
class UserService:
    user_repository: UserRepository
    notification_service: NotificationService
    config: Config

    def find_all(
        self, pagination: Pagination = None, sort_by: str = None, sort_desc: bool = True
    ) -> PaginatedResponse[User]:
        return self.user_repository.find_all(
            pagination=pagination, sort_by=sort_by, sort_desc=sort_desc
        )

    def count_all_by_dict(self, criteria: dict) -> int:
        return self.user_repository.count_all_by_dict(criteria)

    def find_user_by_email(self, email: EmailStr) -> User:
        return self.user_repository.find_one_by_dict({"email": email})
    
    def find_one(self, user_id: PyObjectId) -> User:
        return self.user_repository.find_one(user_id)

    def register_user(self, user: UserCreate) -> User:
        existing_user = self.user_repository.find_one_by_dict({"email": user.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with the current email already exist",
            )
        hashed_password = hash_password(user.password)
        
        # Create personal info if not provided
        personal_info = user.personal_info or PersonalInfo()
        
        # Create contact info if not provided
        contact_info = user.contact_info or ContactInfo(
            email=user.email
        )
        
        created_user = User(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            personal_info=personal_info,
            contact_info=contact_info,
            location_info=user.location_info or LocationInfo(),
            password_hash=hashed_password,
        )
       
        self.notification_service.create_notification(
            user_id=created_user.id,
            content=f"Welcome to the platform {created_user.first_name} {created_user.last_name}",
            notification_type=NotificationType.SYSTEM,
        )

        return self.user_repository.save(created_user)

    def create_admin(self, user: UserCreate) -> User:
        existing_user = self.user_repository.find_one_by_dict({"email": user.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with the current email already exist",
            )
        hashed_password = hash_password(user.password)
        created_user = User(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            password_hash=hashed_password,
            role=Role.ADMIN,
            is_verified=True,
        )
        logger.info(f"Creating admin user: {created_user}")
        return self.user_repository.save(created_user)

    def authenticate_user(self, email: EmailStr, password: str) -> str:
        user = self.user_repository.find_one_by_dict({"email": email})
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect Email or Password",
            )
        user.last_login = datetime.utcnow()
        self.user_repository.save(user)
        return create_access_token({"sub": str(user.id)})

    def validate_token(self, token: str) -> User:
        try:
            payload = decode_token(token)
            user_id = payload.get("sub")
            return self.user_repository.find_one(user_id)
        except Exception:
            raise ValueError("Invalid Token")

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
                user = User(
                    first_name=data.first_name,
                    last_name=data.last_name if data.last_name else "",
                    password_hash="",
                    role=Role.USER,
                    telegram=TelegramData(
                        telegram_id=data.id,
                        first_name=data.first_name,
                        last_name=data.last_name,
                        username=data.username,
                        photo_url=data.photo_url,
                    ),
                )

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

    def update_user_info(self, user_id: PyObjectId, user: User) -> User:
        existing_user = self.find_one(user_id)
        existing_user.first_name = user.first_name
        existing_user.last_name = user.last_name
        
        existing_user.personal_info = user.personal_info
        existing_user.contact_info = user.contact_info
        existing_user.location_info = user.location_info
        existing_user.communication_preferences = user.communication_preferences
        existing_user.privacy_settings = user.privacy_settings
        existing_user.updated_at = datetime.now(timezone.utc)
        return self.user_repository.save(existing_user)

    def get_profile_completion(self, user_id: PyObjectId) -> dict:
        user = self.find_one(user_id)
        return {
            "is_complete": user.is_profile_complete(),
            "completion_percentage": user.get_completion_percentage(),
            "missing_fields": self._get_missing_fields(user)
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
