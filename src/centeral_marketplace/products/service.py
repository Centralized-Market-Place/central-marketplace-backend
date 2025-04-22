from dataclasses import dataclass
from centeral_marketplace.comments.core import Comment, CommentCreate, CommentUpdate
from centeral_marketplace.comments.service import CommentService
from centeral_marketplace.infrastructure.json import PaginatedResponse, Pagination
from centeral_marketplace.products.core import Product
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

    def find_all(
        self,
        pagination: Pagination = None,
        sort_by: str = None,
        sort_desc: bool = True,
        criteria: dict = None,
    ) -> PaginatedResponse[Product]:
        if criteria is None:
            criteria = {}
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
    ):
        self.find_one(product_id)
        criteria = {"product_id": product_id}
        return self.comment_service.find_all(
            pagination=pagination,
            sort_by="created_at",
            sort_desc=sort_desc,
            criteria=criteria,
        )

    def create_post_comment(
        self, user_id: PyObjectId, product_id: PyObjectId, comment_data: CommentCreate
    ) -> Comment:
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
    ) -> Comment:
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

    def find_one(self, product_id: PyObjectId) -> Product:
        product = self.product_repository.find_one(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found",
            )

        return product
