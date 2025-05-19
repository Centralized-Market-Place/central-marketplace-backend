from fastapi import APIRouter
from fastapi_injector import Injected
from .core import PasswordResetRequest, PasswordResetConfirm
from .service import PasswordResetService

password_reset_router = APIRouter(prefix="/password-reset", tags=["password-reset"])

@password_reset_router.post("/request")
async def password_reset_request(
    data: PasswordResetRequest,
    password_reset_service: PasswordResetService = Injected(PasswordResetService),
):
    return password_reset_service.initiate_password_reset(data.email)

@password_reset_router.post("/confirm")
async def password_reset_confirm(
    data: PasswordResetConfirm,
    password_reset_service: PasswordResetService = Injected(PasswordResetService),
):
    return password_reset_service.confirm_password_reset(data.token, data.new_password) 