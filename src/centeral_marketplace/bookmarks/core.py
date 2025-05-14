from centeral_marketplace.infrastructure.json import MongoBaseModel
from core import PyObjectId


class Bookmark(MongoBaseModel):
    user_id: PyObjectId
    product_id: PyObjectId

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
