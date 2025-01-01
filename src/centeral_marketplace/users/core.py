from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Optional, List, Self
from bson import ObjectId

from centeral_marketplace.infrastructure.repository import PrivacyEntity
from core import PyObjectId


@dataclass
class UserBase(PrivacyEntity):
    first_name: str
    last_name: str
    username: str
    # external_user_id: str
    # external_user_name: Optional[str] = None
    image: Optional[str] = None
    
    
@dataclass
class UserBase:
    first_name: str
    last_name: str
    username: str
    # external_user_id: str
    # external_user_name: Optional[str] = None
    password : Optional[str] = None
    image: Optional[str] = None

@dataclass
class UserCreate(UserBase):
    pass

@dataclass
class User(UserBase):
    id: PyObjectId = field(default_factory=PyObjectId)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    password: str = field(default="")
    role: str = field(default="user")

    def to_dict(self) -> dict:
        """Convert the dataclass to a dictionary with `_id` as the alias for `id`."""
        data = self.__dict__.copy()
        if "id" in data:
            data["_id"] = str(data.pop("id")) 
        data.pop("password", None) 
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create a User instance from a dictionary with `_id` as the MongoDB field."""
        data = data.copy()
        if "_id" in data:
            data["id"] = PyObjectId(data.pop("_id"))
        return cls(**data)