from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import EmailStr, BaseModel, Field
from bson import ObjectId


@dataclass
class Role(Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    SELLER = "SELLER"


@dataclass
class UserBase:
    name: str
    email: EmailStr


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


@dataclass
class UserCreate(UserBase):
    password: str = Field(min_length=6)

@dataclass
class TelegramData:
    telegram_id: int                  
    first_name: str                   
    last_name: Optional[str] = None     
    username: Optional[str] = None  
    photo_url: Optional[str] = None 
    auth_date: datetime = field(default_factory=datetime.utcnow)


@dataclass
class User(UserBase):
    id: str = field(default_factory=lambda: str(ObjectId()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    password_hash: str = field(default="")
    image: Optional[str] = None
    role: Role = field(default_factory=lambda: Role.USER)
    last_login: Optional[datetime] = None
    is_verified: bool = False
    telegram: Optional[TelegramData] = None

@dataclass
class UserPublic(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime
    role: Role
    is_verified: bool
    image: Optional[str] = None
    last_login: Optional[datetime] = None
    

@dataclass
class AuthResponse:
    token: str
    user: User

class TelegramLogin(BaseModel):
    telegram_id: int = Field(..., alias="id")
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str
