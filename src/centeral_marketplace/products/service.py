from dataclasses import dataclass
import logging
import traceback

from centeral_marketplace.bookmarks.repository import BookmarkRepository
from centeral_marketplace.channels.core import ChannelAnalytics
from centeral_marketplace.channels.repository import ChannelRepository
from centeral_marketplace.channels.service import ChannelService
from centeral_marketplace.comments.core import (
    CommentCreate,
    CommentUpdate,
    CommentPublic,
)
from centeral_marketplace.comments.service import CommentService
from centeral_marketplace.infrastructure.json import PaginatedResponse, Pagination
from centeral_marketplace.products.core import ProductPublic, UpdateProduct
from centeral_marketplace.products.repository import ProductRepository
from centeral_marketplace.reactions.service import ReactionService
from centeral_marketplace.sellers.service import SellerService
from centeral_marketplace.users.core import User
from fastapi import HTTPException, status
from injector import inject, singleton

from core import PyObjectId

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


@singleton
@inject
@dataclass
class ProductService:
    product_repository: ProductRepository
    comment_service: CommentService
    reaction_service: ReactionService
    bookmark_repository: BookmarkRepository
    channel_repository: ChannelRepository
    channel_service: ChannelService
    seller_service: SellerService

    def find_all(
        self,
        user_id: PyObjectId | None = None,
        pagination: Pagination = None,
        sort_by: str = None,
        sort_desc: bool = True,
        criteria: dict | None = None,
    ) -> PaginatedResponse[ProductPublic]:
        try:
            if criteria is None:
                criteria = {}

            if user_id:
                paginated_product = self.product_repository.find_all_with_user_reaction(
                    user_id=user_id,
                    pagination=pagination,
                    sort_by=sort_by,
                    sort_desc=sort_desc,
                    criteria=criteria,
                )

                paginated_product.items = [
                    self.build_product(product, user_id=user_id)
                    for product in paginated_product.items
                ]
                return paginated_product
            else:
                return self.product_repository.find_all_by_dict(
                    pagination=pagination,
                    sort_by=sort_by,
                    sort_desc=sort_desc,
                    criteria=criteria,
                )
        except Exception as e:
            logger.error(f"Error finding products: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve products",
            ) from e

    def find_all_comments(
        self,
        product_id: PyObjectId,
        pagination: Pagination = None,
        sort_desc: bool = True,
        user_id: PyObjectId | None = None,
    ) -> PaginatedResponse[CommentPublic]:
        try:
            self.find_one(product_id)
            criteria = {"product_id": product_id, "parent_id": None}
            return self.comment_service.find_all(
                user_id=user_id,
                pagination=pagination,
                sort_by="created_at",
                sort_desc=sort_desc,
                criteria=criteria,
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error finding comments for product {product_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve product comments",
            ) from e

    def create_post_comment(
        self, user_id: PyObjectId, product_id: PyObjectId, comment_data: CommentCreate
    ) -> CommentPublic:
        try:
            product = self.find_one(product_id)
            comment = self.comment_service.create_comment(
                user_id=user_id, product_id=product_id, comment_data=comment_data
            )
            product.comments += 1
            self.product_repository.save(product)
            return comment
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error creating comment for product {product_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to create comment",
            ) from e

    def update_post_comment(
        self,
        user_id: PyObjectId,
        product_id: PyObjectId,
        comment_id: PyObjectId,
        comment_data: CommentUpdate,
    ) -> CommentPublic:
        try:
            self.find_one(product_id)
            return self.comment_service.update_comment(
                user_id=user_id, comment_id=comment_id, comment_data=comment_data
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error updating comment {comment_id} for product {product_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to update comment",
            ) from e

    def delete_post_comment(
        self, product_id: PyObjectId, user_id: PyObjectId, comment_id: PyObjectId
    ):
        try:
            product = self.find_one(product_id)
            comment = self.comment_service.delete_comment(
                user_id=user_id, comment_id=comment_id
            )
            product.comments -= 1
            self.product_repository.save(product)
            return comment
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error deleting comment {comment_id} for product {product_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to delete comment",
            ) from e

    def build_product(self, product: ProductPublic, user_id: PyObjectId | None = None):
        try:
            if user_id:
                product.is_bookmarked = (
                    self.bookmark_repository.find_one_by_user_and_product(
                        user_id=user_id, product_id=product.id
                    )
                    is not None
                )
            return product
        except Exception:
            logger.error(
                f"Error building product {product.id}: {traceback.format_exc()}"
            )

            return product

    def find_one(
        self, product_id: PyObjectId, user_id: PyObjectId | None = None
    ) -> ProductPublic:
        try:
            if user_id:
                product = self.product_repository.find_one_with_user_reaction(
                    product_id=product_id, user_id=user_id
                )
            else:
                product = self.product_repository.find_one(product_id)

            if not product:
                logger.error(f"Product with ID {product_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {product_id} not found",
                )

            return self.build_product(product, user_id=user_id)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error finding product {product_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve product",
            ) from e

    def find_bookmarked_products(
        self,
        user_id: PyObjectId,
        pagination: Pagination | None = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
        query: str = None,
    ) -> PaginatedResponse[ProductPublic]:
        try:
            paginated_products = self.product_repository.find_bookmarked_with_query(
                user_id=user_id,
                pagination=pagination,
                sort_by=sort_by,
                sort_desc=sort_desc,
                query=query,
            )
            paginated_products.items = [
                self.build_product(product, user_id=user_id)
                for product in paginated_products.items
            ]
            return paginated_products
        except Exception as e:
            logger.error(
                f"Error finding bookmarked products for user {user_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve bookmarked products",
            ) from e

    def increment_share_count(
        self, product_id: PyObjectId, user_id: PyObjectId
    ) -> ProductPublic:
        try:
            product = self.product_repository.find_one(product_id)
            if not product:
                logger.error(
                    f"Product with ID {product_id} not found for share increment"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {product_id} not found",
                )

            product.shares += 1
            self.product_repository.save(product)
            return product
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error incrementing share count for product {product_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to increment share count",
            ) from e

    def update_product(
        self, product_id: PyObjectId, product_data: UpdateProduct, user: User
    ) -> ProductPublic:
        try:
            product = self.find_one(product_id)
            seller_applications = self.seller_service.get_approved_seller_applications(
                user.id
            )

            user_channel_ids = set(
                [
                    application.seller_info.channel_id
                    for application in seller_applications
                ]
            )
            channel = product.channel

            if (
                str(product.telegram_channel_id) not in user_channel_ids
                or channel.username not in user_channel_ids
            ):
                logger.error(
                    f"User {user.id} attempted to update product {product_id} without permission"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to update this product",
                )

            for key, value in product_data.model_dump(exclude_unset=True).items():
                setattr(product, key, value)

            self.product_repository.save(product)
            return self.find_one(product_id)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error updating product {product_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to update product",
            ) from e

    def delete_product(self, product_id: PyObjectId, user: User) -> None:
        try:
            product = self.find_one(product_id)
            seller_applications = self.seller_service.get_approved_seller_applications(
                user.id
            )

            user_channel_ids = set(
                [
                    seller_info.seller_info.channel_id
                    for seller_info in seller_applications
                ]
            )
            channel = product.channel

            if (
                str(product.telegram_channel_id) not in user_channel_ids
                or channel.username not in user_channel_ids
            ):
                logger.error(
                    f"User {user.id} attempted to delete product {product_id} without permission"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to delete this product",
                )

            self.product_repository.delete_one(product_id)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error deleting product {product_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to delete product",
            ) from e

    def get_channel_analytics(self, channel_id: PyObjectId) -> ChannelAnalytics:
        try:
            channel = self.channel_repository.find_one(channel_id)
            if not channel:
                logger.error(f"Channel with ID {channel_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Channel with ID {channel_id} not found",
                )

            analytics_data = self.product_repository.get_channel_analytics(channel_id)
            return ChannelAnalytics(**analytics_data)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error getting analytics for channel {channel_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve channel analytics",
            ) from e
