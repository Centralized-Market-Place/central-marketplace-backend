from datetime import datetime
from typing import List, Optional
from centeral_marketplace.infrastructure.json import MongoBaseModel
from centeral_marketplace.reactions.core import ReactionType
from centeral_marketplace.channels.core import Channel
from pydantic import (
    NonNegativeInt,
    PositiveInt,
    PositiveFloat,
)
from core import PyObjectId
from pydantic import validator


class Product(MongoBaseModel):
    channel_id: PyObjectId
    message_id: PositiveInt | None = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[PositiveFloat] = None

    @validator("price", pre=True)
    def parse_price(cls, v):
        if isinstance(v, str):
            return float(v.replace(",", ""))
        return v

    images: List[str] = []
    views: NonNegativeInt = 0
    forwards: NonNegativeInt = 0
    summary: Optional[str] = None
    is_available: Optional[bool] = True
    posted_at: Optional[datetime] = None
    upvotes: NonNegativeInt = 0
    downvotes: NonNegativeInt = 0
    shares: NonNegativeInt = 0
    comments: int = 0
    is_bookmarked: Optional[bool] = False
    user_reaction: Optional[ReactionType] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class ProductPublic(MongoBaseModel):
    channel_id: PyObjectId
    message_id: Optional[PositiveInt] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[PositiveFloat] = None
    images: List[str] = []
    views: NonNegativeInt = 0
    forwards: NonNegativeInt = 0
    summary: Optional[str] = None
    is_available: Optional[bool] = True
    posted_at: Optional[datetime] = None
    upvotes: NonNegativeInt = 0
    downvotes: NonNegativeInt = 0
    shares: NonNegativeInt = 0
    comments: int = 0
    is_bookmarked: Optional[bool] = False
    user_reaction: Optional[ReactionType] = None
    channel: Optional[Channel] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
