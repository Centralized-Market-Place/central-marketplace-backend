from datetime import UTC, datetime
import logging
from typing import Any, TypeVar, Generic, Type, Optional, List, Dict
from pydantic import BaseModel

from centeral_marketplace.infrastructure.json import (
    Pagination,
    PaginatedResponse,
)
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import DuplicateKeyError
from pymongo.collection import Collection
from bson import ObjectId

from config import Config
from core import PyObjectId

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())
Entity = TypeVar("Entity", bound=BaseModel)


class MongoDBJsonRepositoryDelegate(Generic[Entity]):
    def __init__(self, collection_name: str, model: Type[Entity], config: Config):
        client = MongoClient(config.mongo_uri)
        db = client[config.database_name]
        self.collection: Collection = db[collection_name]
        self.model: Type[Entity] = model

    def ensure_index(self, field: str, unique: bool = False, name: str = None):
        """Ensure an index on the specified field."""
        index_kwargs = {"unique": unique}
        if name:
            index_kwargs["name"] = name
        index_name = self.collection.create_index([(field, ASCENDING)], **index_kwargs)
        logger.debug("Index '%s' ensured on field '%s'.", index_name, field)

    def ensure_compound_index(self, fields: List[tuple], unique: bool = False, name: str = None):
        """Ensure a compound index on the specified fields."""
        index_kwargs = {"unique": unique}
        if name:
            index_kwargs["name"] = name
        index_name = self.collection.create_index(fields, **index_kwargs)
        logger.debug("Compound index '%s' ensured on fields '%s'.", index_name, fields)

    def ensure_text_index(self, fields: List[str], name: str = None):
        """Ensure a text index on the specified fields."""
        text_fields = [(field, "text") for field in fields]
        index_kwargs = {}
        if name:
            index_kwargs["name"] = name
        index_name = self.collection.create_index(text_fields, **index_kwargs)
        logger.debug("Text index '%s' ensured on fields '%s'.", index_name, fields)

    def _to_oid(self, value: Any) -> ObjectId | Any:
        if value is None or isinstance(value, ObjectId):
            return value
        try:
            return ObjectId(str(value))
        except Exception:
            return value

    def _normalize_for_mongo(self, data: dict) -> dict:
        if data.get("id"):
            data["_id"] = self._to_oid(data.pop("id"))

        for k, v in data.items():
            if k.endswith("_id") and k != "_id":
                data[k] = self._to_oid(data[k])

        return data

    def find_all(
        self,
        pagination: Pagination = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = True,
    ) -> PaginatedResponse[Entity]:
        """Find all entities with optional pagination and sorting."""
        query = {}
        sort_order = DESCENDING if sort_desc else ASCENDING

        cursor = self.collection.find(query)

        if sort_by:
            cursor = cursor.sort(sort_by, sort_order)

        if pagination:
            skip = (pagination.page - 1) * pagination.size
            limit = pagination.size
            cursor = cursor.skip(skip).limit(limit)

        total = self.collection.count_documents(query)
        items = [self.model.model_validate(document) for document in cursor]
        page = pagination.page if pagination else 1
        page_size = pagination.size if pagination else 0
        return PaginatedResponse(
            page=page, page_size=page_size, total=total, items=items
        )

    def save(self, entity: Entity) -> Entity:
        now = datetime.now(UTC)
        entity.updated_at = now

        doc = self._normalize_for_mongo(
            entity.model_dump(exclude_none=True, by_alias=False)
        )

        if "_id" in doc:
            oid = doc["_id"]
            self.collection.replace_one({"_id": oid}, doc, upsert=True)
            entity.id = oid
        else:
            result = self.collection.insert_one(doc)
            entity.id = result.inserted_id

        return entity

    def save_all(self, entities: List[Entity]):
        docs = [
            self._normalize_for_mongo(e.model_dump(exclude_none=True, by_alias=False))
            for e in entities
        ]
        try:
            self.collection.insert_many(docs, ordered=False)
        except DuplicateKeyError as e:
            raise ValueError(f"Duplicate key error: {e}")

    def find_one(self, id: PyObjectId) -> Entity:
        """Find a single entity by ID."""
        document = self.collection.find_one({"_id": ObjectId(id)})
        if not document:
            raise ValueError(f"Entity with ID {id} not found")
        return self.model.model_validate(document)

    def delete_one(self, id: PyObjectId):
        """Delete a single entity by ID."""
        result = self.collection.delete_one({"_id": id})
        if result.deleted_count == 0:
            raise ValueError(f"Entity with ID {id} not found")

    def find_all_by_dict(
        self,
        criteria: Dict,
        pagination: Pagination = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = True,
    ) -> PaginatedResponse[Entity]:
        """Find all entities matching the criteria."""
        sort_order = DESCENDING if sort_desc else ASCENDING

        cursor = self.collection.find(criteria)

        if sort_by:
            cursor = cursor.sort(sort_by, sort_order)

        if pagination:
            skip = (pagination.page - 1) * pagination.size
            limit = pagination.size
            cursor = cursor.skip(skip).limit(limit)

        total = self.collection.count_documents(criteria)
        items = [self.model.model_validate(document) for document in cursor]
        page = pagination.page if pagination else 1
        page_size = pagination.size if pagination else 0
        return PaginatedResponse(
            page=page, page_size=page_size, total=total, items=items
        )

    def count_all_by_dict(self, criteria: Dict) -> int:
        """Count all entities matching the criteria."""
        return self.collection.count_documents(criteria)

    def delete_all(self):
        """Delete all documents in the collection."""
        self.collection.delete_many({})

    def delete_by_dict(self, criteria: Dict):
        """Delete documents matching the criteria."""
        result = self.collection.delete_many(criteria)
        logger.debug(
            "Deleted %d document(s) matching criteria %s",
            result.deleted_count,
            criteria,
        )
        return result.deleted_count

    def find_one_by_dict(self, query: dict) -> Optional[Entity]:
        try:
            document = self.collection.find_one(query)
            return self.model.model_validate(document) if document else None
        except Exception as e:
            logger.error(f"Error finding document: {e}")
            raise
