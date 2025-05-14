from bson import ObjectId
from core import PyObjectId
from pydantic import AliasChoices, BaseModel, Field, PositiveInt
from typing import Annotated, Generic, List, Optional, TypeVar
from datetime import datetime

T = TypeVar("T")


class MongoBaseModel(BaseModel):
    id: PyObjectId = Field(
        default_factory=ObjectId,
        validation_alias=AliasChoices("_id", "id"),
        serialization_alias="id",
    )
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Pagination(BaseModel):
    page: PositiveInt = 1
    size: Annotated[int, Field(gt=0, le=100)]


class PaginatedResponse(BaseModel, Generic[T]):
    page: int
    page_size: int
    total: int
    items: List[T]
