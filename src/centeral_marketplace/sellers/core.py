from datetime import datetime
from enum import Enum
from typing import Optional
from bson import ObjectId
from pydantic import AliasChoices, BaseModel, Field
from core import PyObjectId


class SellerApplicationStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class SellerInfo(BaseModel):
    business_name: str
    tin_number: str
    channel_id: str
    channel_name: str
    government_id: str
    has_bot_admin_access: bool = False
    verified_channel_ownership: bool = False


class SellerApplication(BaseModel):
    id: PyObjectId = Field(
        default_factory=ObjectId,
        validation_alias=AliasChoices("_id", "id"),
        serialization_alias="id",
    )
    user_id: PyObjectId
    seller_info: SellerInfo
    status: SellerApplicationStatus = SellerApplicationStatus.PENDING
    admin_review_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class SellerApplicationCreate(BaseModel):
    business_name: str
    tin_number: str
    channel_id: str
    channel_name: str
    government_id: str


class SellerApplicationReview(BaseModel):
    application_id: PyObjectId
    status: SellerApplicationStatus
    admin_review_notes: Optional[str] = None


class TelegramBotStatusResponse(BaseModel):
    has_bot_admin_access: bool
    verified_channel_ownership: bool
