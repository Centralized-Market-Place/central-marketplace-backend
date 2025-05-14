from typing import Optional
from centeral_marketplace.infrastructure.json import MongoBaseModel
from centeral_marketplace.reactions.core import ReactionType
from core import PyObjectId
from pydantic import BaseModel


class Comment(MongoBaseModel):
    user_id: PyObjectId
    product_id: PyObjectId
    message: str
    likes: int = 0
    dislikes: int = 0
    parent_id: Optional[PyObjectId] = None
    user_reaction: Optional[ReactionType] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class CommentCreate(BaseModel):
    message: str


class CommentUpdate(BaseModel):
    message: Optional[str] = None
