from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from bson import ObjectId
from pydantic import BaseModel, Field, AliasChoices
from core import PyObjectId


class NotificationType(str, Enum):
    COMMENT = "comment"
    LIKE = "like"
    MESSAGE = "message"
    POST = "post"
    NEW_APPLICATION = "new_application"
    APPLICATION_STATUS_UPDATE = "application_status_update"
    SYSTEM = "system"


class Notification(BaseModel):
    id: PyObjectId = Field(
        default_factory=ObjectId,
        validation_alias=AliasChoices("_id", "id"),
        serialization_alias="id",
    )
    user_id: PyObjectId
    content: str
    notification_type: NotificationType
    metadata: Dict[str, Any] = Field(default_factory=dict)
    read: bool = False
    read_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
