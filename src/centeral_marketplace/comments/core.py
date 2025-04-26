from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import AliasChoices, BaseModel, Field
from core import PyObjectId


class Comment(BaseModel):
    id: PyObjectId = Field(
        default_factory=ObjectId,
        validation_alias=AliasChoices("_id", "id"),
        serialization_alias="id",
    )
    user_id: PyObjectId
    product_id: PyObjectId
    message: str
    likes: int = 0
    dislikes: int = 0
    parent_id: Optional[PyObjectId] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class CommentCreate(BaseModel):
    message: str


class CommentUpdate(BaseModel):
    message: Optional[str] = None
