from centeral_marketplace.infrastructure.json import MongoBaseModel
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, Dict, Any
from centeral_marketplace.infrastructure.mongo import PyObjectId


class EmailVerificationToken(MongoBaseModel):
    token: str
    user_id: PyObjectId
    expires_at: Optional[datetime] = None
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationResponse(BaseModel):
    message: str


class VerifyEmailResponse(BaseModel):
    message: str
