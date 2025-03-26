from dataclasses import dataclass
from centeral_marketplace.infrastructure.mongo import MongoDBJsonRepositoryDelegate
from config import Config
from injector import inject, singleton
from centeral_marketplace.reactions.core import Reaction


@inject
@singleton
@dataclass
class ReactionRepository:
    config: Config

    def __post_init__(self):
        self.delegate = MongoDBJsonRepositoryDelegate(
            collection_name="reactions", cls=Reaction, config=self.config
        )

    def save(self, reaction: Reaction):
        return self.delegate.save(reaction)

    def find_one_by_user_and_target(self, user_id: str, target_id: str):
        return self.delegate.find_one_by_dict({"user_id": user_id, "target_id": target_id})

    def delete(self, id: str):
        return self.delegate.delete_one(id)

    def delete_by_user_and_target(self, user_id: str, target_id: str):
        return self.delegate.delete_by_dict({"user_id": user_id, "target_id": target_id})
