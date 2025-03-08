from dataclasses import dataclass
from datetime import datetime
from centeral_marketplace.infrastructure.json import Pagination
from fastapi import HTTPException, status
from injector import inject, singleton

from centeral_marketplace.users.repository import UserRepository
from centeral_marketplace.users.auth import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from centeral_marketplace.users.core import User, UserCreate


@singleton
@inject
@dataclass
class UserService:
    user_repository: UserRepository

    def find_all(
        self, pagination: Pagination = None, sort_by: str = None, sort_desc: bool = True
    ) -> list[User]:
        return self.user_repository.find_all(
            pagination=pagination, sort_by=sort_by, sort_desc=sort_desc
        )

    def count_all_by_dict(self, criteria: dict) -> int:
        return self.user_repository.count_all_by_dict(criteria)
    
    def find_user_by_email(self, email: str) -> User:
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

    def authenticate_user(self, email: str, password: str) -> str:
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
        payload = decode_token(token)
        user_id = payload.get("sub")
        return self.user_repository.find_one(user_id)
