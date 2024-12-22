from dataclasses import dataclass, replace
from datetime import datetime
from typing import Optional, List, Self
from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field

from centeral_marketplace.infrastructure.repository import PrivacyEntity
from core import PyObjectId


@dataclass
class UserBase(PrivacyEntity):
    first_name: str
    last_name: str
    email: EmailStr
    external_user_id: str
    external_user_name: Optional[str] = None
    image: Optional[str] = None
    

class UserCreate(UserBase):
    pass


class User(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "id": "5f7d5b2f5a8e3b3a8c8e3b3a",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "external_user_id": "12345",
                "external_user_name": "johndoe",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "image": "https://example.com/avatar.jpg",
            }
        }
