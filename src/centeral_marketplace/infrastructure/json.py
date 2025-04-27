from pydantic import BaseModel, Field, PositiveInt
from typing import Annotated, Generic, List, TypeVar

T = TypeVar("T")


class Pagination(BaseModel):
    page: PositiveInt = 1
    size: Annotated[int, Field(gt=0, le=100)]


class PaginatedResponse(BaseModel, Generic[T]):
    page: int
    page_size: int
    total: int
    items: List[T]
