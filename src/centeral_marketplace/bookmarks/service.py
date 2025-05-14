from dataclasses import dataclass
from datetime import datetime, UTC
from centeral_marketplace.products.core import Product
from centeral_marketplace.products.service import ProductService
from fastapi import HTTPException, status
from injector import inject, singleton

from centeral_marketplace.bookmarks.core import Bookmark
from centeral_marketplace.bookmarks.repository import BookmarkRepository
from centeral_marketplace.products.repository import ProductRepository
from centeral_marketplace.infrastructure.json import PaginatedResponse, Pagination
from core import PyObjectId


@singleton
@inject
@dataclass
class BookmarkService:
    bookmark_repository: BookmarkRepository
    product_repository: ProductRepository
    product_service: ProductService

    def add_bookmark(self, user_id: PyObjectId, product_id: PyObjectId) -> Bookmark:
        self.product_service.find_one(product_id)
        existing = self.bookmark_repository.find_one_by_user_and_product(
            user_id, product_id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Already bookmarked",
            )

        now = datetime.now(UTC)
        bookmark = Bookmark(
            user_id=user_id, 
            product_id=product_id,
            created_at=now
        )
        return self.bookmark_repository.save(bookmark)

    def remove_bookmark(self, user_id: PyObjectId, product_id: PyObjectId) -> None:
        existing = self.bookmark_repository.find_one_by_user_and_product(
            user_id, product_id
        )
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found"
            )
        self.bookmark_repository.delete_one(existing.id)

    def get_bookmark(self, user_id: PyObjectId, product_id: PyObjectId) -> Bookmark:
        bookmark = self.bookmark_repository.find_one_by_user_and_product(
            user_id, product_id
        )
        if not bookmark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found"
            )
        return bookmark

    def find_bookmarks(
        self,
        user_id: PyObjectId,
        pagination: Pagination | None = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> PaginatedResponse[Bookmark]:
        return self.bookmark_repository.find_all_by_user(
            user_id, pagination=pagination, sort_by=sort_by, sort_desc=sort_desc
        )

    def find_bookmarked_products(
        self,
        user_id: PyObjectId,
        pagination: Pagination | None = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> PaginatedResponse[Product]:
        bookmarks = self.find_bookmarks(user_id, pagination, sort_by, sort_desc)
        product_ids = [bookmark.product_id for bookmark in bookmarks.items]
        products = self.product_repository.find_all_by_ids(product_ids)
        return PaginatedResponse(
            items=products, total=len(products), page=1, size=len(products)
        )
