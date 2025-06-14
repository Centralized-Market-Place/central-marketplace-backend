from datetime import datetime
from typing import List, Optional
from centeral_marketplace.infrastructure.json import MongoBaseModel
from centeral_marketplace.reactions.core import ReactionType
from centeral_marketplace.channels.core import Channel
from pydantic import (
    BaseModel,
    NonNegativeInt,
    PositiveInt,
    PositiveFloat,
)
from core import PyObjectId


class Product(MongoBaseModel):
    channel_id: PyObjectId
    date: datetime
    telegram_channel_id: int
    message_id: PositiveInt | None = None
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[PositiveFloat] = None
    images: List[str] = []
    views: NonNegativeInt = 0
    forwards: NonNegativeInt = 0
    location: Optional[str] = None
    is_available: Optional[bool] = True
    upvotes: NonNegativeInt = 0
    downvotes: NonNegativeInt = 0
    shares: NonNegativeInt = 0
    comments: int = 0
    clicks: NonNegativeInt = 0
    is_updated: Optional[bool] = False
    is_deleted: Optional[bool] = False
    is_bookmarked: Optional[bool] = False
    categories: List[str] = []
    link: List[str] = []
    phone: List[str] = []

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class ProductPublic(MongoBaseModel):
    channel_id: PyObjectId
    telegram_channel_id: int
    date: datetime
    message_id: Optional[PositiveInt] = None
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[PositiveFloat] = None
    images: List[str] = []
    views: NonNegativeInt = 0
    forwards: NonNegativeInt = 0
    location: Optional[str] = None
    clicks: NonNegativeInt = 0
    is_available: Optional[bool] = True
    upvotes: NonNegativeInt = 0
    downvotes: NonNegativeInt = 0
    shares: NonNegativeInt = 0
    comments: int = 0
    is_bookmarked: Optional[bool] = False
    user_reaction: Optional[ReactionType] = None
    channel: Optional[Channel] = None
    link: list[str] = []
    phone: list[str] = []
    categories: list[str] = []

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class UpdateProduct(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[PositiveFloat] = None
    location: Optional[str] = None
    is_available: Optional[bool] = None
    phone: Optional[List[str]] = None
