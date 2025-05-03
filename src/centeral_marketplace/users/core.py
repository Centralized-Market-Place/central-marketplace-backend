from datetime import datetime
from enum import Enum
from typing import Optional
from bson import ObjectId
from pydantic import AliasChoices, BaseModel, EmailStr, Field
from core import PyObjectId
from centeral_marketplace.sellers.core import SellerInfo


class Role(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    SELLER = "SELLER"


class TelegramData(BaseModel):
    telegram_id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: datetime = Field(default_factory=datetime.utcnow)


class UserBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class User(UserBase):
    id: PyObjectId = Field(
        default_factory=ObjectId,
        validation_alias=AliasChoices("_id", "id"),
        serialization_alias="id",
    )
    password_hash: str
    image: Optional[str] = None
    role: Role = Role.USER
    is_verified: bool = False
    last_login: Optional[datetime] = None
    telegram: Optional[TelegramData] = None
    seller_info: Optional[SellerInfo] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class UserPublic(UserBase):
    id: PyObjectId = Field(alias="_id")
    role: Role
    is_verified: bool
    image: Optional[str] = None
    last_login: Optional[datetime] = None
    telegram: Optional[TelegramData] = None
    seller_info: Optional[SellerInfo] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class AuthResponse(BaseModel):
    token: str
    user: User


class TelegramLogin(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str
