from datetime import datetime, UTC
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId

class Notification(BaseModel):
    model_config = ConfigDict(json_encoders={ObjectId: str})
    
    id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    notification_type: str
    data: dict
    read: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat()) 