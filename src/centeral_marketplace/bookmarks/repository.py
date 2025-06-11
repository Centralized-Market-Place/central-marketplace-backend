from dataclasses import dataclass
from typing import Optional
from centeral_marketplace.infrastructure.json import PaginatedResponse, Pagination
from centeral_marketplace.infrastructure.mongo import MongoDBJsonRepositoryDelegate
from config import Config
from injector import inject, singleton
from centeral_marketplace.bookmarks.core import Bookmark
from core import PyObjectId


@singleton
@inject
@dataclass
class BookmarkRepository:
    config: Config

    def __post_init__(self):
        self.delegate = MongoDBJsonRepositoryDelegate(
            collection_name="bookmarks",
            model=Bookmark,
            config=self.config,
        )
    
        self.delegate.ensure_compound_index([("user_id", 1), ("product_id", 1), ("created_at", -1)], unique=True, name="bookmarks_unique_user_product")
        self.delegate.ensure_index("product_id", name="bookmarks_product")
        self.delegate.ensure_compound_index([("user_id", 1), ("created_at", -1)], name="bookmarks_user_created")

    def save(self, bookmark: Bookmark) -> Bookmark:
        return self.delegate.save(bookmark)

    def find_one(self, id: PyObjectId) -> Optional[Bookmark]:
        return self.delegate.find_one(id)

    def find_one_by_user_and_product(
        self, user_id: PyObjectId, product_id: PyObjectId
    ) -> Optional[Bookmark]:
        return self.delegate.find_one_by_dict(
            {"user_id": user_id, "product_id": product_id}
        )

    def delete_one(self, id: PyObjectId) -> None:
        return self.delegate.delete_one(id)

    def delete_by_user_and_product(
        self, user_id: PyObjectId, product_id: PyObjectId
    ) -> int:
        return self.delegate.delete_by_dict(
            {"user_id": user_id, "product_id": product_id}
        )

    def find_all_by_user(
        self,
        user_id: PyObjectId,
        pagination: Pagination | None = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> PaginatedResponse[Bookmark]:
        criteria = {"user_id": user_id}
        return self.delegate.find_all_by_dict(
            criteria=criteria,
            pagination=pagination,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )
