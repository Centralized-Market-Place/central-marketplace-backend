import base64
import jwt
from datetime import datetime, timedelta
from config import settings
import os
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: int = None):
    expire = datetime.utcnow() + (timedelta(seconds=expires_delta) if expires_delta else timedelta(minutes=15))
    data.update({"exp": expire})
    return jwt.encode(data, base64.b64decode(
        settings.jwt_private_key).decode('utf-8'), algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, base64.b64decode(settings.jwt_public_key).decode('UTF-8'), algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")