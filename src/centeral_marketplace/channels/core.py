from datetime import datetime
from typing import Optional
from centeral_marketplace.infrastructure.json import MongoBaseModel
from pydantic import Field


class Channel(MongoBaseModel):
    telegram_id: int
    title: Optional[str] = Field(default="")
    username: Optional[str] = Field(default="")
    description: Optional[str] = Field(default="")
    thumbnail_url: Optional[str] = Field(default="")
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

    class Config:
        from_attributes = True
