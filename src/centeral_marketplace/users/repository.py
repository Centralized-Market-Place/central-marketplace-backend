

from dataclasses import dataclass
from typing import Iterator
from injector import inject, singleton
from centeral_marketplace.infrastructure.mongo import MongoDBJsonRepositoryDelegate
from centeral_marketplace.infrastructure.repository import RepositoryInterface
from centeral_marketplace.users.core import User
from config import Config

@inject
@singleton
@dataclass
class UserRepository(RepositoryInterface[User]):
    config: Config
    def __post_init__(self):
        self.delegate = MongoDBJsonRepositoryDelegate(collection_name="users", cls=User, config=self.config)

    def close(self):
        self.delegate.close()

    def save(self, data: User):
        return self.delegate.save(data)

    def save_all(self, data: list[User]):
        return self.delegate.save_all(data)

    def find_all(self):
        return self.delegate.find_all()

    def find_one(self, id: str):
        return self.delegate.find_one(id)

    def find_one_by_username(self, user_name: str):
        return self.delegate.find_one_by_dict({"username": user_name})

    def delete_one(self, id: str):
        return self.delegate.delete_one(id)

    def find_all_by(self, **kwargs):
        return self.delegate.find_one_by_dict(kwargs)

    def count_all_by_dict(self, criteria):
        return self.delegate.count_all_by_dict(criteria)

    def delete_all(self):
        return self.delegate.delete_all()

    def find_all_by_dict(self, criteria: dict) -> Iterator[User]:
        return self.delegate.find_all_by_dict(criteria)
