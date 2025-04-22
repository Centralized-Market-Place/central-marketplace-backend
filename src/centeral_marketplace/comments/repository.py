from dataclasses import dataclass
from typing import Optional

from centeral_marketplace.infrastructure.json import PaginatedResponse, Pagination
from centeral_marketplace.infrastructure.mongo import MongoDBJsonRepositoryDelegate
from config import Config
from injector import inject, singleton
from centeral_marketplace.comments.core import Comment
from core import PyObjectId


@inject
@singleton
@dataclass
class CommentRepository:
    config: Config

    def __post_init__(self):
        self.delegate = MongoDBJsonRepositoryDelegate(
            collection_name="comments", model=Comment, config=self.config
        )

    def save(self, data: Comment):
        return self.delegate.save(data)

    def save_all(self, data: list[Comment]):
        return self.delegate.save_all(data)

    def find_one(self, id: PyObjectId) -> Optional[Comment]:
        return self.delegate.find_one(id)

    def find_all(
        self, sort_by: str = None, sort_desc: bool = True, pagination: Pagination = None
    ) -> PaginatedResponse[Comment]:
        return self.delegate.find_all(
            pagination=pagination, sort_by=sort_by, sort_desc=sort_desc
        )

    def find_all_by(
        self,
        sort_by: str = None,
        sort_desc: bool = True,
        pagination: Pagination = None,
        **kwargs,
    ) -> PaginatedResponse[Comment]:
        return self.delegate.find_all_by_dict(
            criteria=kwargs, pagination=pagination, sort_by=sort_by, sort_desc=sort_desc
        )

    def find_one_by_dict(self, criteria: dict) -> Comment:
        return self.delegate.find_one_by_dict(criteria)

    def delete_one(self, id: PyObjectId):
        return self.delegate.delete_one(id)

    def find_all_by_dict(
        self,
        criteria: dict,
        sort_by: str = None,
        sort_desc: bool = True,
        pagination: Pagination = None,
    ) -> PaginatedResponse[Comment]:
        return self.delegate.find_all_by_dict(
            criteria=criteria,
            pagination=pagination,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )

    def count_all_by_dict(self, criteria: dict) -> int:
        return self.delegate.count_all_by_dict(criteria)

    def delete_all(self):
        return self.delegate.delete_all()
