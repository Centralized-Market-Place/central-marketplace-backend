from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import AliasChoices, BaseModel, Field, field_validator

from core import PyObjectId


class Channel(BaseModel):
    id: PyObjectId = Field(
            default_factory=ObjectId,
            validation_alias=AliasChoices("_id", "id"),
            serialization_alias="id",
        )
    telegram_id: str
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

     
    
    @field_validator('telegram_id')
    @classmethod
    def convert_telegram_id_to_str(cls, v):
        if isinstance(v, int):
            return str(v)
        return v
    
    class Config:
        from_attributes = True
