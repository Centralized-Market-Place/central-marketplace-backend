from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from centeral_marketplace.infrastructure.json import MongoBaseModel
from core import PyObjectId
from pydantic import Field


class NotificationType(str, Enum):
    COMMENT = "comment"
    LIKE = "like"
    MESSAGE = "message"
    POST = "post"
    NEW_APPLICATION = "new_application"
    APPLICATION_STATUS_UPDATE = "application_status_update"
    SYSTEM = "system"


class Notification(MongoBaseModel):
    user_id: PyObjectId
    content: str
    notification_type: NotificationType
    metadata: Dict[str, Any] = Field(default_factory=dict)
    read: bool = False
    read_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
