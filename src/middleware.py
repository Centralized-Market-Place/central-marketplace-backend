from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi_injector import Injected
from fastapi.security import OAuth2PasswordBearer
from centeral_marketplace.users.core import User
from centeral_marketplace.users.service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login", auto_error=False)


async def get_current_user(
    token: str = Security(oauth2_scheme),
    user_service: UserService = Injected(UserService),
):
    try:
        return user_service.validate_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


async def get_current_user_optional(
    token: Optional[str] = Security(oauth2_scheme),
    user_service: UserService = Injected(UserService),
) -> Optional[User]:
    if token is None:
        return None
    try:
        return user_service.validate_token(token)
    except Exception:
        return None


def require_role(required_roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role.value not in required_roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return current_user

    return role_checker
