from typing import Annotated
from centeral_marketplace.users.auth import create_access_token
from fastapi import APIRouter, Depends
from fastapi_injector import Injected

from centeral_marketplace.users.service import UserService
from centeral_marketplace.infrastructure.json import (
    Pagination,
    PaginatedResponse,
)
from centeral_marketplace.users.core import (
    User,
    UserCreate,
    UserLogin,
    AuthResponse,
    UserPublic,
    ProfileResponse,
    ProfileUpdate,
    PasswordUpdate,
    TelegramLogin,
)
from middleware import get_current_user, require_role


users_router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@users_router.get("/", response_model=PaginatedResponse[User])
async def get_users(
    current_user: Annotated[User, Depends(require_role("ADMIN"))],
    page: int = 1,
    page_size: int = 10,
    sort_by: str = None,
    sort_desc: bool = True,
    user_service: UserService = Injected(UserService),
):
    pagination = Pagination(page=page, size=page_size)

    users = user_service.find_all(
        pagination=pagination, sort_by=sort_by, sort_desc=sort_desc
    )

    return users


@users_router.post("/register", response_model=UserPublic)
async def register_user(
    user: UserCreate,
    user_service: UserService = Injected(UserService),
):
    return user_service.register_user(user)


@users_router.post("/login", response_model=AuthResponse)
async def login_user(
    user: UserLogin,
    user_service: UserService = Injected(UserService),
):
    access_token = user_service.authenticate_user(user.email, user.password)
    user = user_service.find_user_by_email(user.email)
    return AuthResponse(token=access_token, user=user)


@users_router.get("/me", response_model=UserPublic)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user


@users_router.post("/telegram", response_model=AuthResponse)
async def telegram_auth(
    telegram_data: TelegramLogin,
    user_service: UserService = Injected(UserService),
):
    user = user_service.login_telegram_user(telegram_data)
    access_token = create_access_token({"sub": str(user.id)})
    return AuthResponse(token=access_token, user=user)


@users_router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Injected(UserService),
):
    """Get current user's profile"""
    return user_service.get_profile(str(current_user.id))


@users_router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    profile_update: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Injected(UserService)
) -> ProfileResponse:
    """Update current user's profile"""
    return user_service.update_profile(str(current_user.id), profile_update)


@users_router.patch("/profile/password")
async def update_password(
    password_update: PasswordUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Injected(UserService)
):
    """Update current user's password"""
    user_service.update_password(str(current_user.id), password_update)
    return {"message": "Password updated successfully"}


@users_router.get("/profile/{user_id}", response_model=ProfileResponse)
async def get_public_profile(
    user_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get public profile by user ID"""
    return user_service.get_public_profile(user_id)

