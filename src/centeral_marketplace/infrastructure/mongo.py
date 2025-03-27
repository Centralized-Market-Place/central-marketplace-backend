import logging
from typing import TypeVar, Generic, Type, Optional, List, Dict

from centeral_marketplace.infrastructure.json import (
    Pagination,
    create_rest_converter,
    PaginatedResponse,
)
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import DuplicateKeyError
from pymongo.collection import Collection
from bson import ObjectId

from config import Config

logger = logging.getLogger(__name__)
Entity = TypeVar("Entity")


class DomainConverter(Generic[Entity]):
    def __init__(self, cls: Type[Entity]):
        self.converter = create_rest_converter()
        self.cls = cls

    def encode(self, entity: Entity) -> Dict:
        """Converts an entity to a dictionary for MongoDB storage."""
        data = self.converter.unstructure(entity)
        return data

    def decode(self, data: Dict) -> Entity:
        """Converts a MongoDB document to an entity."""
        data = data.copy()
        if "_id" in data:
            data["id"] = str(data.pop("_id"))
        return self.converter.structure(data, self.cls)


class MongoDBJsonRepositoryDelegate(Generic[Entity]):
    def __init__(self, collection_name: str, cls: Type[Entity], config: Config):
        connection_string = config.mongo_uri
        database_name = config.database_name
        client = MongoClient(connection_string)
        database = client[database_name]
        self.collection: Collection = database[collection_name]
        self.converter = DomainConverter(cls=cls)
        self.cls = cls

    def ensure_index(self, field: str, unique: bool = False):
        """Ensure an index on the specified field."""
        index_name = self.collection.create_index([(field, ASCENDING)], unique=unique)
        logger.debug("Index '%s' ensured on field '%s'.", index_name, field)

    def ensure_compound_index(self, fields: List[tuple], unique: bool = False):
        index_name = self.collection.create_index(fields, unique=unique)
        logger.debug("Compound index '%s' ensured on fields '%s'.", index_name, fields)

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
        items = [self.converter.decode(document) for document in cursor]
        return PaginatedResponse(
            page=pagination.page, page_size=pagination.size, total=total, items=items
        )

    def save(self, entity: Entity):
        """Insert or update an entity."""
        data = self.converter.encode(entity)

        if hasattr(entity, "id") and entity.id:
            _id = ObjectId(entity.id)
            data["_id"] = _id
            self.collection.replace_one({"_id": _id}, data, upsert=True)
        else:
            data["_id"] = ObjectId()
            result = self.collection.insert_one(data)
            entity.id = str(result.inserted_id)

        return entity

    def find_one(self, id: str) -> Entity:
        """Find a single entity by ID."""
        document = self.collection.find_one({"_id": ObjectId(id)})
        if not document:
            raise ValueError(f"Entity with ID {id} not found")
        return self.converter.decode(document)

    def delete_one(self, id: str):
        """Delete a single entity by ID."""
        result = self.collection.delete_one({"_id": ObjectId(id)})
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
        items = [self.converter.decode(document) for document in cursor]
        return PaginatedResponse(
            page=pagination.page, page_size=pagination.size, total=total, items=items
        )

    def count_all_by_dict(self, criteria: Dict) -> int:
        """Count all entities matching the criteria."""
        return self.collection.count_documents(criteria)

    def delete_all(self):
        """Delete all documents in the collection."""
        self.collection.delete_many({})

    def save_all(self, entities: List[Entity]):
        """Insert or update multiple entities."""

        data = [self.converter.encode(entity) for entity in entities]
        try:
            self.collection.insert_many(data)
        except DuplicateKeyError as e:
            raise ValueError(f"Duplicate key error: {e}")

    def find_one_by_dict(self, query: dict) -> Optional[Entity]:
        try:
            document = self.collection.find_one(query)
            return self.converter.decode(document) if document else None
        except Exception as e:
            logger.error(f"Error finding document: {e}")
            raise
