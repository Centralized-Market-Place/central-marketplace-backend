from dataclasses import dataclass
from datetime import datetime, UTC
import logging
import traceback

from centeral_marketplace.products.core import Product
from centeral_marketplace.products.service import ProductService
from fastapi import HTTPException, status
from injector import inject, singleton

from centeral_marketplace.bookmarks.core import Bookmark
from centeral_marketplace.bookmarks.repository import BookmarkRepository
from centeral_marketplace.products.repository import ProductRepository
from centeral_marketplace.infrastructure.json import PaginatedResponse, Pagination
from core import PyObjectId

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


@singleton
@inject
@dataclass
class BookmarkService:
    bookmark_repository: BookmarkRepository
    product_repository: ProductRepository
    product_service: ProductService

    def add_bookmark(self, user_id: PyObjectId, product_id: PyObjectId) -> Bookmark:
        try:
            # Verify product exists
            self.product_service.find_one(product_id)

            existing = self.bookmark_repository.find_one_by_user_and_product(
                user_id, product_id
            )
            if existing:
                logger.error(
                    f"User {user_id} attempted to bookmark already bookmarked product {product_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Product is already bookmarked",
                )

            now = datetime.now(UTC)
            bookmark = Bookmark(user_id=user_id, product_id=product_id, created_at=now)
            saved_bookmark = self.bookmark_repository.save(bookmark)
            logger.info(f"User {user_id} bookmarked product {product_id}")
            return saved_bookmark
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error adding bookmark for user {user_id} and product {product_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to add bookmark",
            ) from e

    def remove_bookmark(self, user_id: PyObjectId, product_id: PyObjectId) -> None:
        try:
            existing = self.bookmark_repository.find_one_by_user_and_product(
                user_id, product_id
            )
            if not existing:
                logger.error(
                    f"User {user_id} attempted to remove non-existent bookmark for product {product_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found"
                )

            self.bookmark_repository.delete_one(existing.id)
            logger.info(f"User {user_id} removed bookmark for product {product_id}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error removing bookmark for user {user_id} and product {product_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to remove bookmark",
            ) from e

    def get_bookmark(self, user_id: PyObjectId, product_id: PyObjectId) -> Bookmark:
        try:
            bookmark = self.bookmark_repository.find_one_by_user_and_product(
                user_id, product_id
            )
            if not bookmark:
                logger.error(
                    f"Bookmark not found for user {user_id} and product {product_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found"
                )
            return bookmark
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error getting bookmark for user {user_id} and product {product_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve bookmark",
            ) from e

    def find_bookmarks(
        self,
        user_id: PyObjectId,
        pagination: Pagination | None = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> PaginatedResponse[Bookmark]:
        try:
            result = self.bookmark_repository.find_all_by_user(
                user_id, pagination=pagination, sort_by=sort_by, sort_desc=sort_desc
            )
            logger.info(f"Retrieved {len(result.items)} bookmarks for user {user_id}")
            return result
        except Exception as e:
            logger.error(
                f"Error finding bookmarks for user {user_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve bookmarks",
            ) from e

    def find_bookmarked_products(
        self,
        user_id: PyObjectId,
        pagination: Pagination | None = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> PaginatedResponse[Product]:
        try:
            bookmarks = self.find_bookmarks(user_id, pagination, sort_by, sort_desc)
            product_ids = [bookmark.product_id for bookmark in bookmarks.items]
            products = self.product_repository.find_all_by_ids(product_ids)
            result = PaginatedResponse(
                items=products, total=len(products), page=1, size=len(products)
            )
            logger.info(
                f"Retrieved {len(products)} bookmarked products for user {user_id}"
            )
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error finding bookmarked products for user {user_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve bookmarked products",
            ) from e
