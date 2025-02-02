from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from bson import ObjectId


@dataclass
class Category:
    id: str = field(default_factory=lambda: str(ObjectId()))
    name: str
    description: Optional[str] = None


@dataclass
class Product:
    id: str = field(default_factory=lambda: str(ObjectId()))
    name: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None
    price: Optional[float] = None
    categories: list[Category] = field(default_factory=list)
    is_available: Optional[bool] = True
    images: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    channel_id: str
    posted_at: Optional[datetime] = None
