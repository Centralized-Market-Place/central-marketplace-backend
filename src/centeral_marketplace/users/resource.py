from typing import Annotated, Dict
from centeral_marketplace.email.core import (
    ResendVerificationRequest,
    ResendVerificationResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi_injector import Injected

from centeral_marketplace.users.service import UserService
from centeral_marketplace.infrastructure.json import (
    Pagination,
    PaginatedResponse,
)
from centeral_marketplace.users.core import (
    Role,
    User,
    UserCreate,
    UserLogin,
    AuthResponse,
    UserPublic,
    TelegramLogin,
    UserProfileUpdate,
    TelegramEmailAddRequest,
    TelegramPasswordSetRequest,
)
from centeral_marketplace.users.auth import create_access_token
from middleware import get_current_user, require_role


users_router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@users_router.get("/", response_model=PaginatedResponse[User])
async def get_users(
    current_user: Annotated[User, Depends(require_role([Role.SUPER_ADMIN.value]))],
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
    background_tasks: BackgroundTasks,
    user_service: UserService = Injected(UserService),
):
    return user_service.register_user(user, background_tasks=background_tasks)


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


@users_router.patch("/profile", response_model=User)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: UserService = Injected(UserService),
):
    return user_service.update_profile(current_user.id, profile_data)


@users_router.get("/profile/completion", response_model=Dict)
async def get_profile_completion(
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: UserService = Injected(UserService),
):
    return user_service.get_profile_completion(current_user.id)


@users_router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(
    data: VerifyEmailRequest,
    user_service: UserService = Injected(UserService),
):
    return user_service.verify_email(data.token)


@users_router.post("/resend-verification", response_model=ResendVerificationResponse)
async def resend_verification(
    data: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    user_service: UserService = Injected(UserService),
):
    return user_service.resend_verification(
        data.email, background_tasks=background_tasks
    )


@users_router.post("/telegram/add-email", response_model=UserPublic)
async def request_telegram_email_add(
    data: TelegramEmailAddRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    background_tasks: BackgroundTasks,
    user_service: UserService = Injected(UserService),
):
    return user_service.request_telegram_email_add(
        current_user.id, data.email, background_tasks=background_tasks
    )


@users_router.post("/telegram/complete-setup", response_model=UserPublic)
async def complete_telegram_email_setup(
    data: TelegramPasswordSetRequest,
    user_service: UserService = Injected(UserService),
):
    return user_service.complete_telegram_email_password_setup(
        data.token, data.password
    )
