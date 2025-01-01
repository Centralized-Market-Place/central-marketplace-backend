
from fastapi import APIRouter, Depends
from fastapi_injector import Injected

from centeral_marketplace.users.service import UserService
from centeral_marketplace.infrastructure.json import RestConverter
from centeral_marketplace.users.core import UserCreate


users_router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@users_router.get("/")
async def get_users(
    user_service: UserService = Injected(UserService),
    converter: RestConverter = Injected(RestConverter),
):
    users =  user_service.find_all()
    return converter.unstructure(users)

@users_router.post("/register")
async def register_user(
    user: UserCreate, 
    user_service: UserService = Injected(UserService)
):
    new_user = user_service.register_user(
        first_name=user.first_name,
        last_name=user.last_name,
        username = user.username,
        password=user.password
    )
    return {"message": "User registered successfully", "user": new_user.to_dict()}

@users_router.post("/login")
async def login_user(
    username: str, 
    password: str, 
    user_service: UserService = Injected(UserService)
):
    token = user_service.authenticate_user(username, password)
    return {"access_token": token, "token_type": "bearer"}
