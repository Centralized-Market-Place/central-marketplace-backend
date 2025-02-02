from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi_injector import Injected
from fastapi.responses import JSONResponse

from centeral_marketplace.users.service import UserService
from centeral_marketplace.infrastructure.json import (
    Pagination,
    RestConverter,
    PaginatedResponse,
)
from centeral_marketplace.users.core import User, UserCreate, UserLogin
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


@users_router.post("/register")
async def register_user(
    user: UserCreate,
    user_service: UserService = Injected(UserService),
    converter: RestConverter = Injected(RestConverter),
):
    new_user = user_service.register_user(user)
    new_user.password = ""
    return converter.unstructure(new_user)


@users_router.post("/login")
async def login_user(
    user: UserLogin, user_service: UserService = Injected(UserService)
):
    access_token = user_service.authenticate_user(user.email, user.password)
    return JSONResponse({"token": access_token, "email": user.email}, status_code=200)
