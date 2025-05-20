from typing import Annotated, Dict
from centeral_marketplace.email.core import EmailVerificationToken, ResendVerificationRequest, ResendVerificationResponse, VerifyEmailRequest, VerifyEmailResponse
from centeral_marketplace.email.repository import EmailVerificationTokenRepository
from centeral_marketplace.users.auth import create_access_token
from centeral_marketplace.users.repository import UserRepository
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_injector import Injected
import secrets
from datetime import datetime, UTC, timedelta

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
    UserProfileUpdate,
)
from middleware import get_current_user, require_role
from centeral_marketplace.email.service import EmailService


users_router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@users_router.get("/", response_model=PaginatedResponse[User])
async def get_users(
    current_user: Annotated[User, Depends(require_role(["SUPER_ADMIN"]))],
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
    email_verification_token_repository: EmailVerificationTokenRepository = Injected(EmailVerificationTokenRepository),
    user_repository: UserRepository = Injected(UserRepository),
):  
   
    token_obj = email_verification_token_repository.get_token(data.token)
    

    if not token_obj:
        return VerifyEmailResponse(message="Invalid or expired token")
    
    user = user_repository.find_one(token_obj.user_id)
    
    if not user:
        return VerifyEmailResponse(message="User not found")
    
    if user.verification_status.email_verified or user.is_verified:
        return VerifyEmailResponse(message="Email already verified")
    
    if token_obj.expires_at:
        expires_at = token_obj.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < datetime.now(UTC):
            email_verification_token_repository.delete_token(data.token)
            return VerifyEmailResponse(message="Token expired. Please request a new verification email.")
    
    user.verification_status.email_verified = True
    user.is_verified = True
    user_repository.save(user)
    print(f"we have the user saved {user}")
    email_verification_token_repository.delete_token(data.token)
    return VerifyEmailResponse(message="Email verified successfully")


@users_router.post("/resend-verification", response_model=ResendVerificationResponse)
async def resend_verification(
    data: ResendVerificationRequest,
    email_verification_token_repository: EmailVerificationTokenRepository = Injected(EmailVerificationTokenRepository),
    user_service: UserService = Injected(UserService),
    email_service: EmailService = Injected(EmailService),
):
    user = user_service.user_repository.find_one_by_dict({"email": data.email})
    if not user:
        return ResendVerificationResponse(message="User not found")
    if user.verification_status.email_verified or user.is_verified:
        return ResendVerificationResponse(message="Email is already verified")

    token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    expires_at = now + timedelta(hours=24)
    verification_token = EmailVerificationToken(
        token=token,
        user_id=user.id,
        created_at=now,
        expires_at=expires_at
    )
    
    email_verification_token_repository.save_token(verification_token)
    verification_link = f"https://centeral-marketplace-webapp-cso4pcdpd.vercel.app/verify-email?token={token}"
    email_service.send_verification_email(user.email, verification_link, user_name=user.first_name)
    return ResendVerificationResponse(message="Verification email resent")
