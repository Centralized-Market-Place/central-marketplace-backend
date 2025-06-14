from datetime import datetime
from typing import Optional
from centeral_marketplace.infrastructure.json import MongoBaseModel
from pydantic import Field


class Category(MongoBaseModel):
    category_name: str = Field(default="")

    class Config:
        from_attributes = True
