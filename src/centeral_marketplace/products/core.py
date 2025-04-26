from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from centeral_marketplace.reactions.core import ReactionType
from pydantic import (
    AliasChoices,
    BaseModel,
    Field,
    NonNegativeInt,
    PositiveInt,
    PositiveFloat,
)
from core import PyObjectId


class Product(BaseModel):
    id: PyObjectId = Field(
        default_factory=ObjectId,
        validation_alias=AliasChoices("_id", "id"),
        serialization_alias="id",
    )
    channel_id: int
    message_id: PositiveInt
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[PositiveFloat] = None
    images: List[str] = []
    views: NonNegativeInt = 0
    forwards: NonNegativeInt = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    summary: Optional[str] = None
    is_available: Optional[bool] = True
    posted_at: Optional[datetime] = None
    upvotes: NonNegativeInt = 0
    downvotes: NonNegativeInt = 0
    shares: NonNegativeInt = 0
    comments: NonNegativeInt = 0
    user_reaction: Optional[ReactionType] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
