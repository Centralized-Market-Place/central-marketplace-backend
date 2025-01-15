
from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi_injector import Injected

from centeral_marketplace.users.service import UserService
from centeral_marketplace.infrastructure.json import RestConverter
from centeral_marketplace.users.core import Token, User, UserCreate, UserLogin
from middleware import require_role


users_router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@users_router.get("/test")
async def get_users(
    current_user: Annotated[User, Depends(require_role("user"))],
    user_service: UserService = Injected(UserService),
    converter: RestConverter = Injected(RestConverter),
):
    return {"current_user": converter.unstructure(current_user)}

@users_router.post("/register")
async def register_user(
    user: UserCreate, 
    user_service: UserService = Injected(UserService),
    converter: RestConverter = Injected(RestConverter),
):
    new_user = user_service.register_user(
        user
    )
    new_user.password = ''
    return converter.unstructure(new_user)

@users_router.post("/login")
async def login_user(
    user: UserLogin,
    user_service: UserService = Injected(UserService)
):
    token = user_service.authenticate_user(user.username, user.password)
    return Token(access_token=token, token_type="bearer")
