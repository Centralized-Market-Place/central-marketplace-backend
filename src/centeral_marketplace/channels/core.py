from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import AliasChoices, BaseModel, Field

from core import PyObjectId


class Channel(BaseModel):
    id: PyObjectId = Field(
            default_factory=ObjectId,
            validation_alias=AliasChoices("_id", "id"),
            serialization_alias="id",
        )
    title: Optional[str] = Field(default="")
    username: Optional[str] = Field(default="")
    description: Optional[str] = Field(default="")
    thumbnail_url: Optional[str] = Field(default="")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    total_products: int = 0
    participants: int = 0
    trust_score: int = 0
    verified: bool = False
    restricted: bool = False
    scam: bool = False
    has_geo: bool = False
    has_link: bool = False
    date_created: Optional[datetime] = None
    broadcast: bool = False
    telegram_id: int = 0

    class Config:
        from_attributes = True
