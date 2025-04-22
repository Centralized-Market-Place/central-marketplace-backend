from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from core import PyObjectId


class ReactionTarget(str, Enum):
    PRODUCT = "product"
    COMMENT = "comment"


class ReactionType(str, Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"
    LIKE = "like"
    DISLIKE = "dislike"


class Reaction(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    target_id: PyObjectId
    target_type: ReactionTarget
    reaction_type: ReactionType
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class CreateReaction(BaseModel):
    target_id: PyObjectId
    target_type: ReactionTarget
    reaction_type: ReactionType
