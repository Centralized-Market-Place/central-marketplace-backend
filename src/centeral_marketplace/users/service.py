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
from centeral_marketplace.users.core import User, UserCreate


@singleton
@inject
@dataclass
class UserService:

    user_repository: UserRepository

    def find_all(self):
        return self.user_repository.find_all()

    def register_user(self, user: UserCreate) -> User:
        existing_user = self.user_repository.find_one_by_dict({"username": user.username})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with the current userName already exist",
            )
        hashed_password = hash_password(user.password)
        created_user = User(
            name=user.name,
            username=user.username,
            password=hashed_password,
        )
        return self.user_repository.save(created_user)
        
        

    def authenticate_user(self, username: str, password: str) -> str:
        user = self.user_repository.find_one_by_dict({"username": username})
        if not user or not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect Email or Password",
            )
        return create_access_token({"sub": {"user_id": user.id, "username": user.username}, "name": user.name})

    def validate_token(self, token: str) -> User:
        payload = decode_token(token)
        user_id = payload.get("sub", {}).get("user_id")
        return self.user_repository.find_one(user_id)
