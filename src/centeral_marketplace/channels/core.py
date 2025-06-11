from datetime import datetime
from typing import Optional
from centeral_marketplace.infrastructure.json import MongoBaseModel
from pydantic import BaseModel


class Channel(MongoBaseModel):
    telegram_id: int
    title: Optional[str] = None
    username: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
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

class UpdateChannel(BaseModel):
    title: Optional[str] = None
    description_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

class ChannelAnalytics(BaseModel):
    total_products: int
    total_views: int
    average_price: float
    availability_percentage: float