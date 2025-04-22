from dataclasses import dataclass
import logging
import traceback
from typing import Optional

from centeral_marketplace.comments.core import Comment, CommentCreate, CommentUpdate
from centeral_marketplace.comments.repository import CommentRepository
from centeral_marketplace.infrastructure.json import PaginatedResponse, Pagination
from centeral_marketplace.reactions.service import ReactionService
from fastapi import HTTPException, status
from injector import inject, singleton

from core import PyObjectId

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


@singleton
@inject
@dataclass
class CommentService:
    comment_repository: CommentRepository
    reaction_service: ReactionService

    def find_all(
        self,
        pagination: Pagination = None,
        sort_by: str = None,
        sort_desc: bool = True,
        criteria: dict = None,
    ) -> PaginatedResponse[Comment]:
        if criteria is None:
            criteria = {}
        return self.comment_repository.find_all_by_dict(
            pagination=pagination,
            sort_by=sort_by,
            sort_desc=sort_desc,
            criteria=criteria,
        )

    def find_one(self, comment_id: PyObjectId) -> Comment:
        comment = self.comment_repository.find_one(comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"comment with ID {comment_id} Not found",
            )

        return comment

    def create_comment(
        self,
        user_id: PyObjectId,
        comment_data: CommentCreate,
        parent_id: Optional[PyObjectId] = None,
        product_id: Optional[PyObjectId] = None,
    ) -> Comment:
        try:
            if parent_id:
                parent_comment = self.find_one(parent_id)
                comment = Comment(
                    user_id=user_id,
                    product_id=parent_comment.product_id,
                    parent_id=parent_id,
                    **comment_data.model_dump(),
                )
            else:
                comment = Comment(
                    user_id=user_id,
                    product_id=product_id,
                    parent_id=parent_id,
                    **comment_data.model_dump(),
                )
            return self.comment_repository.save(comment)
        except Exception as e:
            message = f"Error creating comment: {traceback.format_exc()}"
            logger.error(message)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to create comment",
            ) from e

    def update_comment(
        self,
        user_id: PyObjectId,
        comment_id: PyObjectId,
        comment_data: CommentUpdate,
        parent_id: Optional[PyObjectId] = None,
    ) -> Comment:
        try:
            if parent_id:
                self.find_one(parent_id)
            comment = self.comment_repository.find_one(comment_id)
            if not comment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
                )
            if comment.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="user not the autor of the comment",
                )
            for key, value in comment_data.model_dump(exclude_unset=True).items():
                setattr(comment, key, value)
            return self.comment_repository.save(comment)
        except Exception as e:
            message = f"Error updating comment: {traceback.format_exc()}"
            logger.error(message)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to update comment",
            ) from e

    def delete_comment(self, user_id: PyObjectId, comment_id: PyObjectId):
        try:
            comment = self.comment_repository.find_one(comment_id)
            if not comment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
                )
            if comment.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="user not the author of the comment",
                )
            return self.comment_repository.delete_one(comment_id)
        except Exception as e:
            message = f"Error deleting comment: {traceback.format_exc()}"
            logger.error(message)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to delete comment",
            ) from e
