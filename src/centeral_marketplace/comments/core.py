from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel


class CommentBase(BaseModel):
    message: str
    likes: int = 0
    dislikes: int = 0


@dataclass
class Comment(CommentBase):
    id: str = field(default_factory=lambda: str(ObjectId()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    user_id: str
    post_id: str
    parent_id: Optional[str] = None


class CommentCreate(CommentBase):
    pass


class CommentUpdate(CommentBase):
    message: Optional[str] = None
    likes: Optional[int] = None
    dislikes: Optional[int] = None
