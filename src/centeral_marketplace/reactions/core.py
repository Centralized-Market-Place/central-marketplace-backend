from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic import BaseModel


class ReactionTarget(str, Enum):
    PRODUCT = "product"
    COMMENT = "comment"


class ReactionType(str, Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"
    LIKE = "like"
    DISLIKE = "dislike"


@dataclass
class Reaction:
    user_id: str
    target_id: str
    target_type: ReactionTarget
    reaction_type: ReactionType
    id: str = field(default_factory=lambda: str(ObjectId()))
    created_at: datetime = field(default_factory=datetime.utcnow)


class CreateReaction(BaseModel):
    reaction_type: ReactionType
    target_id: str
    target_type: ReactionTarget
