"""Repository and Persistence related interfaces.

Please do not implement any logic in this file. This file is only for
interfaces.

Interfaces are used to define the contract of the repository and related
persistence operations.

It should not contain any implementation details or behavior.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Iterator


from core import PyObjectId


class EntityNotFound(Exception):
    pass


class Entity(ABC):
    id: PyObjectId


class PrivacyEntity(Entity, ABC):
    pass


EntityType = TypeVar("EntityType", bound=Entity)
PrivacyEntityType = TypeVar("PrivacyEntityType", bound=PrivacyEntity)


class RepositoryInterface(ABC, Generic[EntityType]):
    @abstractmethod
    def find_all(self) -> Iterator[EntityType]:
        pass

    @abstractmethod
    def save(self, entity: EntityType) -> EntityType:
        pass

    @abstractmethod
    def find_one(self, id: PyObjectId) -> EntityType:
        pass

    @abstractmethod
    def delete_one(self, id: PyObjectId):
        pass

    @abstractmethod
    def find_all_by(self, **kwargs) -> Iterator[EntityType]:
        pass

    @abstractmethod
    def find_all_by_dict(self, criteria: dict) -> Iterator[EntityType]:
        pass

    @abstractmethod
    def count_all_by_dict(self, criteria: dict) -> int:
        pass

    @abstractmethod
    def delete_all(self):
        pass

    @abstractmethod
    def save_all(self, entities: list[EntityType]):
        pass


class PrivacyRepositoryInterface(RepositoryInterface[PrivacyEntityType], ABC):
    pass
