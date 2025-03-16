from dataclasses import dataclass
from injector import inject, singleton
from centeral_marketplace.infrastructure.mongo import MongoDBJsonRepositoryDelegate
from centeral_marketplace.infrastructure.repository import RepositoryInterface
from centeral_marketplace.channels.core import Channel
from config import Config

@inject
@singleton
@dataclass
class ChannelRepository(RepositoryInterface[Channel]):
    config: Config

    def __post_init__(self):
        self.delegate = MongoDBJsonRepositoryDelegate(
            collection_name="channels", cls=Channel, config=self.config
        )

    def close(self):
        self.delegate.close()

    def save(self, data: Channel):
        return self.delegate.save(data)

    def save_all(self, data: list[Channel]):
        return self.delegate.save_all(data)

    def find_all(
        self, sort_by: str = None, sort_desc: bool = True, pagination=None
    ):
        return self.delegate.find_all(
            pagination=pagination, sort_by=sort_by, sort_desc=sort_desc
        )

    def find_one(self, id: int):
        document = self.delegate.collection.find_one({"id": id})
        if document:
            document.pop("_id", None) 
            return self.delegate.converter.decode(document)
        return None


    def find_all_by(
        self,
        sort_by: str = None,
        sort_desc: bool = True,
        pagination=None,
        **kwargs,
    ):
        return self.delegate.find_all_by_dict(
            criteria=kwargs, pagination=pagination, sort_by=sort_by, sort_desc=sort_desc
        )

    def find_one_by_dict(self, criteria: dict):
        document = self.collection.find_one(criteria)
        if document:
            document.pop("_id", None)
            return self.converter.decode(document)
        return None
    def delete_one(self, id: str):
        return self.delegate.delete_one(id)

    def find_all_by_dict(
        self,
        criteria: dict,
        pagination=None,
        sort_by: str | None = None,
        sort_desc: bool = True,
    ):
        return self.delegate.find_all_by_dict(
            criteria=criteria,
            pagination=pagination,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )

    def count_all_by_dict(self, criteria):
        return self.delegate.count_all_by_dict(criteria)

    def delete_all(self):
        return self.delegate.delete_all()
