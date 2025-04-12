from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Channel:
    id: int
    title: Optional[str] = ""
    username: Optional[str] = ""
    description: Optional[str] = ""
    thumbnail_url: Optional[str] = ""
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
