from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel


class CommentBase(BaseModel):
    message: str


@dataclass
class Comment:
    user_id: str
    product_id: str
    message: str
    id: str = field(default_factory=lambda: str(ObjectId()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    likes: int = 0
    dislikes: int = 0
    parent_id: Optional[str] = None


class CommentCreate(CommentBase):
    pass


class CommentUpdate(CommentBase):
    message: Optional[str] = None
