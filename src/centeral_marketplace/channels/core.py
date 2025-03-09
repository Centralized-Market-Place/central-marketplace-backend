from dataclasses import dataclass
from datetime import datetime

@dataclass
class Channel:
    id: str
    name: str
    description: str = None
    thumbnailUrl: str = None
    createdAt: datetime = None
    updatedAt: datetime = None
    totalProducts: int = None
    subscribers: int = None
    trustScore: int = None
