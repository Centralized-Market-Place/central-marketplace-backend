from dataclasses import dataclass
from centeral_marketplace.infrastructure.mongo import MongoDBJsonRepositoryDelegate
from config import Config
from injector import inject, singleton
from centeral_marketplace.reactions.core import Reaction
from pymongo import ASCENDING

from core import PyObjectId


@inject
@singleton
@dataclass
class ReactionRepository:
    config: Config

    def __post_init__(self):
        self.delegate = MongoDBJsonRepositoryDelegate(
            collection_name="reactions", model=Reaction, config=self.config
        )
        self.delegate.ensure_compound_index(
            [
                ("user_id", ASCENDING),
                ("target_id", ASCENDING),
            ],
            unique=True,
        )

    def save(self, reaction: Reaction):
        return self.delegate.save(reaction)

    def find_one_by_user_and_target(self, user_id: PyObjectId, target_id: PyObjectId):
        return self.delegate.find_one_by_dict(
            {"user_id": user_id, "target_id": target_id}
        )

    def delete(self, id: PyObjectId):
        return self.delegate.delete_one(id)
    
    def delete_all(self):
        return self.delegate.delete_all()

    def delete_by_user_and_target(
        self, user_id: PyObjectId, target_id: PyObjectId
    ) -> int:
        return self.delegate.delete_by_dict(
            {"user_id": user_id, "target_id": target_id}
        )
