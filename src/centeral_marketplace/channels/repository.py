from dataclasses import dataclass
from injector import inject, singleton

from centeral_marketplace.infrastructure.json import PaginatedResponse
from centeral_marketplace.infrastructure.mongo import MongoDBJsonRepositoryDelegate
from centeral_marketplace.infrastructure.repository import RepositoryInterface
from centeral_marketplace.channels.core import Channel
from config import Config
from core import PyObjectId


@inject
@singleton
@dataclass
class ChannelRepository(RepositoryInterface[Channel]):
    config: Config

    def __post_init__(self):
        self.delegate = MongoDBJsonRepositoryDelegate(
            collection_name="channels", model=Channel, config=self.config
        )
        self.delegate.ensure_index("telegram_id")
        self.delegate.ensure_index("username")
        self.delegate.ensure_text_index(
            ["title", "description"], name="channels_text_search"
        )
        self.delegate.ensure_index("created_at", name="channels_created_at")

    def save(self, data: Channel):
        return self.delegate.save(data)

    def save_all(self, data: list[Channel]):
        return self.delegate.save_all(data)

    def find_all(self, sort_by: str = None, sort_desc: bool = True, pagination=None):
        criteria = {
            "is_deleted": {"$in": [False, None]},
            "is_suspended": {"$in": [False, None]},
        }
        return self.delegate.find_all(
            criteria=criteria,
            pagination=pagination,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )

    def find_one(self, id: PyObjectId):
        criteria = {
            "is_deleted": {"$in": [False, None]},
            "is_suspended": {"$in": [False, None]},
            "_id": id,
        }
        return self.delegate.find_one_by_dict(criteria)

    def find_all_by(
        self,
        sort_by: str = None,
        sort_desc: bool = True,
        pagination=None,
        **kwargs,
    ):
        criteria = {
            "is_deleted": {"$in": [False, None]},
            "is_suspended": {"$in": [False, None]},
            **kwargs,
        }
        return self.delegate.find_all_by_dict(
            criteria=criteria,
            pagination=pagination,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )

    def find_one_by_dict(self, criteria: dict):
        criteria = {
            "is_deleted": {"$in": [False, None]},
            "is_suspended": {"$in": [False, None]},
            **criteria,
        }
        return self.delegate.find_one_by_dict(criteria)

    def delete_one(self, id: PyObjectId):
        return self.delegate.delete_one(id)

    def find_all_by_dict(
        self,
        criteria: dict,
        pagination=None,
        sort_by: str | None = None,
        sort_desc: bool = True,
    ) -> PaginatedResponse[Channel]:
        criteria = {
            "is_deleted": {"$in": [False, None]},
            "is_suspended": {"$in": [False, None]},
            **criteria,
        }
        return self.delegate.find_all_by_dict(
            criteria=criteria,
            pagination=pagination,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )

    def count_all_by_dict(self, criteria):
        criteria = {
            "is_deleted": {"$in": [False, None]},
            "is_suspended": {"$in": [False, None]},
            **criteria,
        }
        return self.delegate.count_all_by_dict(criteria)

    def delete_all(self):
        return self.delegate.delete_all()
