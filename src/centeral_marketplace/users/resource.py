from typing import Annotated
from centeral_marketplace.users.auth import create_access_token
from fastapi import APIRouter, Depends
from fastapi_injector import Injected

from centeral_marketplace.users.service import UserService
from centeral_marketplace.infrastructure.json import (
    Pagination,
    RestConverter,
    PaginatedResponse,
)
from centeral_marketplace.users.core import TelegramLogin, User, UserCreate, UserLogin, AuthResponse, UserPublic
from middleware import require_role


users_router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@users_router.get("/")
async def get_users(
    current_user: Annotated[User, Depends(require_role("ADMIN"))],
    page: int = 1,
    page_size: int = 10,
    sort_by: str = None,
    sort_desc: bool = True,
    user_service: UserService = Injected(UserService),
    converter: RestConverter = Injected(RestConverter),
):
    pagination = Pagination(page=page, size=page_size)

    users = list(
        user_service.find_all(
            pagination=pagination, sort_by=sort_by, sort_desc=sort_desc
        )
    )
    total = user_service.count_all_by_dict({})

    return {
        "data": PaginatedResponse(
            page=page,
            page_size=page_size,
            total=total,
            items=converter.unstructure(users),
        )
    }


@users_router.post("/register",response_model=UserPublic)
async def register_user(
    user: UserCreate,
    user_service: UserService = Injected(UserService),
    converter: RestConverter = Injected(RestConverter),
):
    new_user = user_service.register_user(user)
    return converter.unstructure(new_user)

@users_router.post("/login", response_model=AuthResponse)
async def login_user(
    user: UserLogin, user_service: UserService = Injected(UserService),
      converter: RestConverter = Injected(RestConverter),
):
    access_token = user_service.authenticate_user(user.email, user.password)
    user = user_service.find_user_by_email(user.email)
    return AuthResponse(token=access_token, user=converter.unstructure(user))

@users_router.get("/me", response_model=UserPublic)
async def get_me(
    current_user: Annotated[User, Depends()],
    user_service: UserService = Injected(UserService),
    converter: RestConverter = Injected(RestConverter),
):
    return converter.unstructure(current_user)

@users_router.post("/telegram", response_model=AuthResponse)
async def telegram_auth(
    telegram_data: TelegramLogin,
    user_service: UserService = Injected(UserService),
    converter: RestConverter = Injected(RestConverter),
):
    user = user_service.verify_telegram_auth(telegram_data)
    access_token = create_access_token({"sub": user.id})
    return AuthResponse(token=access_token, user=converter.unstructure(user))
