import logging
from typing import TypeVar, Generic, Type, Iterator, Optional, List, Dict

from fastapi import Depends
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import DuplicateKeyError
from pymongo.collection import Collection
from pymongo.database import Database
from bson import ObjectId
from injector import singleton, provider, inject

from config import Config

logger = logging.getLogger(__name__)
Entity = TypeVar("Entity")


@singleton
@provider
@inject
def provide_database(config: Config) -> Database:
    connection_string = config.mongo_uri
    database_name = config.database_name
    client = MongoClient(connection_string)
    return client[database_name]

class DomainConverter(Generic[Entity]):
    def __init__(self, cls: Type[Entity]):
        self.cls = cls

    def encode(self, entity: Entity) -> Dict:
        """Converts an entity to a dictionary for MongoDB storage."""
        return entity.__dict__

    def decode(self, data: Dict) -> Entity:
        """Converts a MongoDB document to an entity."""
        data = data.copy()
        if '_id' in data:
            data['id'] = str(data.pop('_id')) 
        return self.cls(**data)


class MongoDBJsonRepositoryDelegate(Generic[Entity]):
    def __init__(
        self,
        collection_name: str,
        cls: Type[Entity],
        config: Config
    ):
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

    def find_all(
        self, 
        pagination: Optional[Dict] = None, 
        sort_by: Optional[str] = None, 
        sort_desc: bool = True
    ) -> Iterator[Entity]:
        """Find all entities with optional pagination and sorting."""
        query = {}
        sort_order = DESCENDING if sort_desc else ASCENDING

        cursor = self.collection.find(query)

        if sort_by:
            cursor = cursor.sort(sort_by, sort_order)

        if pagination:
            skip = (pagination.get("page", 1) - 1) * pagination.get("size", 10)
            limit = pagination.get("size", 10)
            cursor = cursor.skip(skip).limit(limit)

        for document in cursor:
            yield self.converter.decode(document)

    def save(self, entity: Entity):
        """Insert or update an entity."""
        if not hasattr(entity, "id") or not entity.id:
            raise ValueError("Entity must have an 'id' attribute")

        data = self.converter.encode(entity)

        self.collection.insert_one(data)

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
        pagination: Optional[Dict] = None, 
        sort_by: Optional[str] = None, 
        sort_desc: bool = True
    ) -> Iterator[Entity]:
        """Find all entities matching the criteria."""
        sort_order = DESCENDING if sort_desc else ASCENDING

        cursor = self.collection.find(criteria)

        if sort_by:
            cursor = cursor.sort(sort_by, sort_order)

        if pagination:
            skip = (pagination.get("page", 1) - 1) * pagination.get("size", 10)
            limit = pagination.get("size", 10)
            cursor = cursor.skip(skip).limit(limit)

        for document in cursor:
            yield self.converter.decode(document)

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

    def close(self):
        """Clean up resources (not required for MongoDB in most cases)."""
        pass
