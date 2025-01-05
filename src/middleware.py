from fastapi import HTTPException, Security, Depends, Injected
from fastapi.security import OAuth2PasswordBearer
from src.centeral_marketplace.users.core import User
from src.centeral_marketplace.users.service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

async def get_current_user(
    token: str = Security(oauth2_scheme),
    user_service: UserService = Injected(UserService)
):
    try:
        return user_service.validate_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

def require_role(required_role: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(status_code=403, detail="Forbidden")
        return current_user
    return role_checker
