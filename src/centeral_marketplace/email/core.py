from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from centeral_marketplace.infrastructure.mongo import PyObjectId
from pydantic import Field


class EmailVerificationToken(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    token: str
    user_id: PyObjectId
    created_at: datetime
    expires_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ResendVerificationRequest(BaseModel):
    email: EmailStr

class VerifyEmailRequest(BaseModel):
    token: str

class ResendVerificationResponse(BaseModel):
    message: str

class VerifyEmailResponse(BaseModel):
    message: str
