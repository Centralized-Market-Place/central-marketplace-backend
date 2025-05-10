from dataclasses import dataclass
from typing import List
from centeral_marketplace.infrastructure.json import Pagination, PaginatedResponse
from injector import inject, singleton
from centeral_marketplace.infrastructure.mongo import MongoDBJsonRepositoryDelegate
from centeral_marketplace.infrastructure.repository import RepositoryInterface
from centeral_marketplace.sellers.core import SellerApplication
from config import Config
from core import PyObjectId


@singleton
@inject
@dataclass
class SellerApplicationRepository(RepositoryInterface[SellerApplication]):
    config: Config

    def __post_init__(self):
        self.delegate = MongoDBJsonRepositoryDelegate(
            collection_name="seller_applications", model=SellerApplication, config=self.config
        )
        self.delegate.ensure_index("user_id", unique=False)
        self.delegate.ensure_compound_index([("user_id", 1), ("seller_info.channel_id", 1)], unique=True)

    def save(self, data: SellerApplication):
        return self.delegate.save(data)

    def save_all(self, data: list[SellerApplication]):
        return self.delegate.save_all(data)

    def find_all(
        self, sort_by: str = None, sort_desc: bool = True, pagination: Pagination = None
    ) -> PaginatedResponse[SellerApplication]:
        return self.delegate.find_all(
            pagination=pagination, sort_by=sort_by, sort_desc=sort_desc
        )

    def find_one(self, id: PyObjectId):
        return self.delegate.find_one(id)

    def find_all_by(
        self,
        sort_by: str = None,
        sort_desc: bool = True,
        pagination: Pagination = None,
        **kwargs,
    ) -> PaginatedResponse[SellerApplication]:
        return self.delegate.find_all_by_dict(
            criteria=kwargs, pagination=pagination, sort_by=sort_by, sort_desc=sort_desc
        )

    def find_one_by_dict(self, criteria: dict) -> SellerApplication:
        return self.delegate.find_one_by_dict(criteria)

    def delete_one(self, id: PyObjectId):
        return self.delegate.delete_one(id)

    def find_all_by_dict(
        self,
        criteria: dict,
        pagination=None,
        sort_by: str | None = None,
        sort_desc: bool = True,
    ) -> PaginatedResponse[SellerApplication]:
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

    def find_by_user_id(self, user_id: PyObjectId) -> List[SellerApplication]:
        return self.find_all_by_dict({"user_id": user_id}).items 