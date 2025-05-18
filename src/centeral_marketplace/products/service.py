from dataclasses import dataclass
from centeral_marketplace.bookmarks.repository import BookmarkRepository
from centeral_marketplace.comments.core import CommentCreate, CommentUpdate, CommentPublic
from centeral_marketplace.comments.service import CommentService
from centeral_marketplace.infrastructure.json import PaginatedResponse, Pagination
from centeral_marketplace.products.core import  ProductPublic
from centeral_marketplace.products.repository import ProductRepository
from centeral_marketplace.reactions.service import ReactionService
from fastapi import HTTPException, status
from injector import inject, singleton

from core import PyObjectId


@singleton
@inject
@dataclass
class ProductService:
    product_repository: ProductRepository
    comment_service: CommentService
    reaction_service: ReactionService
    bookmark_repository: BookmarkRepository

    def find_all(
        self,
        user_id: PyObjectId | None = None,
        pagination: Pagination = None,
        sort_by: str = None,
        sort_desc: bool = True,
        criteria: dict = None,
    ) -> PaginatedResponse[ProductPublic]:
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

    def find_all_comments(
        self,
        product_id: PyObjectId,
        pagination: Pagination = None,
        sort_desc: bool = True,
        user_id: PyObjectId | None = None,
    ) -> PaginatedResponse[CommentPublic]:
        self.find_one(product_id)
        criteria = {"product_id": product_id, "parent_id": None}
        return self.comment_service.find_all(
            user_id=user_id,
            pagination=pagination,
            sort_by="created_at",
            sort_desc=sort_desc,
            criteria=criteria,
        )

    def create_post_comment(
        self, user_id: PyObjectId, product_id: PyObjectId, comment_data: CommentCreate
    ) -> CommentPublic:
        product = self.find_one(product_id)
        comment = self.comment_service.create_comment(
            user_id=user_id, product_id=product_id, comment_data=comment_data
        )
        product.comments += 1
        self.product_repository.save(product)
        return comment

    def update_post_comment(
        self,
        user_id: PyObjectId,
        product_id: PyObjectId,
        comment_id: PyObjectId,
        comment_data: CommentUpdate,
    ) -> CommentPublic:
        self.find_one(product_id)
        return self.comment_service.update_comment(
            user_id=user_id, comment_id=comment_id, comment_data=comment_data
        )

    def delete_post_comment(
        self, product_id: PyObjectId, user_id: PyObjectId, comment_id: PyObjectId
    ):
        product = self.find_one(product_id)
        comment = self.comment_service.delete_comment(
            user_id=user_id, comment_id=comment_id
        )
        product.comments -= 1
        self.product_repository.save(product)
        return comment

    def build_product(self, product: ProductPublic, user_id: PyObjectId | None = None):
        if user_id:
            product.is_bookmarked = (
                self.bookmark_repository.find_one_by_user_and_product(
                    user_id=user_id, product_id=product.id
                )
                is not None
            )

        return product

    def find_one(
        self, product_id: PyObjectId, user_id: PyObjectId | None = None
    ) -> ProductPublic:
        if user_id:
            product = self.product_repository.find_one_with_user_reaction(
                product_id=product_id, user_id=user_id
            )

        else:
            product = self.product_repository.find_one(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found",
            )

        return self.build_product(product, user_id=user_id)

    def find_bookmarked_products(
        self,
        user_id: PyObjectId,
        pagination: Pagination | None = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
        query: str = None,
    ) -> PaginatedResponse[ProductPublic]:
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
        
    def increment_share_count(self, product_id: PyObjectId, user_id: PyObjectId) -> ProductPublic:
        product = self.product_repository.find_one(product_id)
        product.shares += 1
        self.product_repository.save(product)
        return product
