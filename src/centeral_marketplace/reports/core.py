from datetime import datetime
from enum import Enum
from typing import Optional
from centeral_marketplace.infrastructure.json import MongoBaseModel
from pydantic import BaseModel
from core import PyObjectId


class ReportType(str, Enum):
    SCAM = "SCAM"
    NOT_RELATED = "NOT_RELATED"
    INAPPROPRIATE = "INAPPROPRIATE"
    SPAM = "SPAM"
    FAKE_PRODUCT = "FAKE_PRODUCT"
    MISLEADING = "MISLEADING"
    OTHER = "OTHER"


class ReportTarget(str, Enum):
    PRODUCT = "PRODUCT"
    CHANNEL = "CHANNEL"


class ReportStatus(str, Enum):
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Report(MongoBaseModel):
    reporter_id: PyObjectId
    target_id: PyObjectId
    target_type: ReportTarget
    report_type: ReportType
    message: Optional[str] = None
    status: ReportStatus = ReportStatus.PENDING
    reviewed_by: Optional[PyObjectId] = None
    reviewed_at: Optional[datetime] = None
    admin_notes: Optional[str] = None
    reporter_name: Optional[str] = None
    target_title: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}


class ReportCreate(BaseModel):
    target_id: PyObjectId
    target_type: ReportTarget
    report_type: ReportType
    message: Optional[str] = None


class ReportReview(BaseModel):
    status: ReportStatus
    admin_notes: Optional[str] = None

    class Config:
        use_enum_values = True

class ReportStatistics(BaseModel):
    total_reports: int
    pending_reports: int
    approved_reports: int
    rejected_reports: int
