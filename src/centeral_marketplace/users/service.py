from dataclasses import dataclass
from datetime import datetime
import hashlib
import hmac
import logging
import time

from pydantic import EmailStr

from centeral_marketplace.infrastructure.json import Pagination
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
)

logger = logging.getLogger(__name__)


@singleton
@inject
@dataclass
class UserService:
    user_repository: UserRepository
    config: Config

    def find_all(
        self, pagination: Pagination = None, sort_by: str = None, sort_desc: bool = True
    ) -> list[User]:
        return self.user_repository.find_all(
            pagination=pagination, sort_by=sort_by, sort_desc=sort_desc
        )

    def count_all_by_dict(self, criteria: dict) -> int:
        return self.user_repository.count_all_by_dict(criteria)

    def find_user_by_email(self, email: EmailStr) -> User:
        return self.user_repository.find_one_by_dict({"email": email})

    def register_user(self, user: UserCreate) -> User:
        existing_user = self.user_repository.find_one_by_dict({"email": user.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with the current email already exist",
            )
        hashed_password = hash_password(user.password)
        created_user = User(
            name=user.name,
            email=user.email,
            password_hash=hashed_password,
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
            name=user.name,
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
        return create_access_token({"sub": user.id})

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
            if not self.verify_telegram_auth(data):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Telegram Auth",
                )

            if time.time() - data.auth_date > 86400:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Telegram Auth Expired",
                )
            user = self.user_repository.find_one_by_dict({"telegram.id": data.id})
            if not user:
                user = User(
                    name=data.first_name + " " + data.last_name
                    if data.last_name
                    else data.first_name,
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
