from dataclasses import dataclass
from fastapi import HTTPException, status
from injector import inject, singleton

from centeral_marketplace.users.repository import UserRepository
from centeral_marketplace.users.auth import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from centeral_marketplace.users.core import User


@singleton
@inject
@dataclass
class UserService:

    user_repository: UserRepository

    def find_all(self):
        return self.user_repository.find_all()

    def register_user(self, first_name, last_name, username, password):
        user = self.user_repository.find_one_by_username(username)
        if user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with the current userName already exist",
            )
        hashed_password = hash_password(password)
        user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=hashed_password,
        )
        self.user_repository.save(user)
        return user

    def authenticate_user(self, username: str, password: str) -> str:
        user = self.user_repository.find_one_by_username(username)
        if not user or not verify_password(password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect Email or Password",
            )
        return create_access_token({"user_id": str(user["id"])})

    def validate_token(self, token: str) -> User:
        payload = decode_token(token)
        user_id = payload.get("user_id")
        return self.user_repository.find_one(user_id)
