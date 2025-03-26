from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from bson import ObjectId


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
    id: str = field(default_factory=lambda: str(ObjectId()))
    user_id: str
    target_id: str
    target_type: ReactionTarget
    reaction_type: ReactionType
    created_at: datetime = field(default_factory=datetime.utcnow)
