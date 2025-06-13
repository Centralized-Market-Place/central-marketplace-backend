from datetime import datetime
from enum import Enum
from typing import Optional
from centeral_marketplace.infrastructure.json import MongoBaseModel
from pydantic import BaseModel, EmailStr, Field
from core import PyObjectId
from centeral_marketplace.users.core import Role


class InvitationStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class AdminInvitation(MongoBaseModel):
    email: EmailStr
    invited_by: PyObjectId
    role: Role
    status: InvitationStatus = InvitationStatus.PENDING
    token: str
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    invited_by_name: str

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class AdminInvitationCreate(BaseModel):
    email: EmailStr
    role: Role = Role.ADMIN


class AdminInvitationAccept(BaseModel):
    token: str
    password: str = Field(..., min_length=6)
    first_name: str
    last_name: Optional[str] = None
