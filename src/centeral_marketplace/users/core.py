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


class SocialMediaLinks(BaseModel):
    twitter: Optional[str] = None
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    linkedin: Optional[str] = None
    website: Optional[str] = None


class ProfileSettings(BaseModel):
    is_profile_public: bool = True
    show_email: bool = False
    show_last_login: bool = True
    show_social_links: bool = True


class User(UserBase):
    id: PyObjectId = Field(
        default_factory=ObjectId,
        validation_alias=AliasChoices("_id", "id"),
        serialization_alias="id",
    )
    password_hash: str
    image: Optional[str] = None
    bio: Optional[str] = None
    role: Role = Role.USER
    is_verified: bool = False
    last_login: Optional[datetime] = None
    telegram: Optional[TelegramData] = None
    social_links: Optional[SocialMediaLinks] = None
    settings: ProfileSettings = Field(default_factory=ProfileSettings)
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


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    image: Optional[str] = None
    social_links: Optional[SocialMediaLinks] = None
    settings: Optional[ProfileSettings] = None


class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


class ProfileResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    name: str
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    image: Optional[str] = None
    role: Role
    is_verified: bool
    last_login: Optional[datetime] = None
    telegram: Optional[TelegramData] = None
    social_links: Optional[SocialMediaLinks] = None
    settings: ProfileSettings = Field(default_factory=ProfileSettings)
    created_at: datetime
    updated_at: datetime
    profile_completion: float = 0.0

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        json_schema_extra = {
            "example": {
                "_id": "67fc18604f1d21bec5c556a4",
                "name": "InternWarrior",
                "email": "yonas@gmail.com",
                "bio": None,
                "image": None,
                "role": "USER",
                "is_verified": False,
                "last_login": "2025-05-08T17:18:12.679000",
                "telegram": None,
                "social_links": None,
                "settings": {
                    "is_profile_public": True,
                    "show_email": False,
                    "show_last_login": True,
                    "show_social_links": True
                },
                "created_at": "2025-04-13T20:02:40.788000",
                "updated_at": "2025-04-13T20:02:40.788000",
                "profile_completion": 40.0
            }
        }
