from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

@dataclass
class Role(Enum):
    ADMIN = "admin"
    USER = "user"

class Token(BaseModel):
    access_token: str
    token_type: str

@dataclass
class UserLogin:
    username: str
    password: str

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
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    password: str = field(default="")
    role: Role =  field(default_factory=lambda: Role.USER)
    id: Optional[str] = field(default=None)