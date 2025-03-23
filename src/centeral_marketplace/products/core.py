from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple
from bson import ObjectId


@dataclass
class Category:
    name: str
    id: str = field(default_factory=lambda: str(ObjectId()))
    description: Optional[str] = None


@dataclass
class Product:
    channel_id: str
    message_id: int
    forwards: int
    views: int
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
    posted_at: Optional[datetime] = None
    upvotes: int = 0
    downvotes: int = 0
    shares: int = 0
    reactions: List[Tuple[str, int]] = field(default_factory=list)
