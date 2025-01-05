from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from centeral_marketplace.infrastructure.repository import PrivacyEntity
from core import PyObjectId

@dataclass
class Role(Enum):
    ADMIN = "admin"
    USER = "user"
    
@dataclass
class UserBase:
    name: str
    username: str
    image: Optional[str] = None

@dataclass
class UserCreate(UserBase):
    password : Optional[str] = None

@dataclass
class User(UserBase):
    id: PyObjectId = field(default_factory=PyObjectId)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    password: str = field(default="")
    role: list[Role] = field(default_factory=list)