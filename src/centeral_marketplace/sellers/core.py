from enum import Enum
from typing import Optional
from centeral_marketplace.infrastructure.json import MongoBaseModel
from pydantic import BaseModel
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


class SellerApplication(MongoBaseModel):
    user_id: PyObjectId
    seller_info: SellerInfo
    status: SellerApplicationStatus = SellerApplicationStatus.PENDING
    admin_review_notes: Optional[str] = None

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

class SellerApplicationUpdate(BaseModel):
    business_name: Optional[str] = None
    tin_number: Optional[str] = None
    government_id: Optional[str] = None


class SellerApplicationReview(BaseModel):
    application_id: PyObjectId
    status: SellerApplicationStatus
    admin_review_notes: Optional[str] = None


class TelegramBotStatusResponse(BaseModel):
    has_bot_admin_access: bool
    verified_channel_ownership: bool


class SellerAnalytics(BaseModel):
    total_channels: int
    total_products: int
    total_views: int
    average_price: float
    availability_percentage: float
