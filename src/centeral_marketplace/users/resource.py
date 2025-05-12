from typing import Annotated, Optional, Dict
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
    TelegramLogin,
    PersonalInfo,
    ContactInfo,
    LocationInfo,
    CommunicationPreferences,
    PrivacySettings,
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


@users_router.put("/profile/personal-info", response_model=User)
async def update_personal_info(
    personal_info: PersonalInfo,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: UserService = Injected(UserService),
):
    """Update user's personal information"""
    return user_service.update_personal_info(current_user.id, personal_info)


@users_router.put("/profile/contact-info", response_model=User)
async def update_contact_info(
    contact_info: ContactInfo,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: UserService = Injected(UserService),
):
    """Update user's contact information"""
    return user_service.update_contact_info(current_user.id, contact_info)


@users_router.put("/profile/location-info", response_model=User)
async def update_location_info(
    location_info: LocationInfo,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: UserService = Injected(UserService),
):
    """Update user's location information"""
    return user_service.update_location_info(current_user.id, location_info)


@users_router.put("/profile/communication-preferences", response_model=User)
async def update_communication_preferences(
    preferences: CommunicationPreferences,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: UserService = Injected(UserService),
):
    """Update user's communication preferences"""
    return user_service.update_communication_preferences(current_user.id, preferences)


@users_router.put("/profile/privacy-settings", response_model=User)
async def update_privacy_settings(
    settings: PrivacySettings,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: UserService = Injected(UserService),
):
    """Update user's privacy settings"""
    return user_service.update_privacy_settings(current_user.id, settings)


@users_router.get("/profile/completion", response_model=Dict)
async def get_profile_completion(
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: UserService = Injected(UserService),
):
    """Get user's profile completion status"""
    return user_service.get_profile_completion(current_user.id)
