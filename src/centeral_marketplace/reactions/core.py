from enum import Enum
from centeral_marketplace.infrastructure.json import MongoBaseModel
from pydantic import BaseModel
from core import PyObjectId


class ReactionTarget(str, Enum):
    PRODUCT = "product"
    COMMENT = "comment"


class ReactionType(str, Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"
    LIKE = "like"
    DISLIKE = "dislike"


class Reaction(MongoBaseModel):
    user_id: PyObjectId
    target_id: PyObjectId
    target_type: ReactionTarget
    reaction_type: ReactionType

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class CreateReaction(BaseModel):
    target_id: PyObjectId
    target_type: ReactionTarget
    reaction_type: ReactionType
