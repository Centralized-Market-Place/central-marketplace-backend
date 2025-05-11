from enum import Enum
from pydantic import BaseModel


class FileType(str, Enum):
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    PDF = "pdf"


class SignedUrlRequest(BaseModel):
    file_type: FileType
    folder: str = "uploads"


class SignedUrlResponse(BaseModel):
    signature: str
    timestamp: int
    cloud_name: str
    api_key: str
    folder: str
    resource_type: str 