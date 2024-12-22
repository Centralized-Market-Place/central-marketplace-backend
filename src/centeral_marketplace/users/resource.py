
from fastapi import APIRouter, Depends
from fastapi_injector import Injected

from centeral_marketplace.users.service import UserService


users_router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@users_router.get("/")
async def get_users(
    user_service: UserService = Injected(UserService),
):
    return user_service.find_all()
