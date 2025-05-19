from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from core import PyObjectId

class PasswordResetToken(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    token: str
    user_id: PyObjectId
    created_at: datetime
    expires_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6) 