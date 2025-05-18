from dataclasses import dataclass
import logging
import traceback

from datetime import datetime, UTC

from centeral_marketplace.comments.core import Comment, CommentCreate, CommentUpdate, CommentPublic
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
        user_id: PyObjectId | None = None,
        pagination: Pagination = None,
        sort_by: str = None,
        sort_desc: bool = True,
        criteria: dict = None,
    ) -> PaginatedResponse[CommentPublic]:
        criteria = criteria or {}
        if user_id:
            return self.comment_repository.find_all_with_user_reaction(
                user_id=user_id,
                criteria=criteria,
                pagination=pagination,
                sort_by=sort_by,
                sort_desc=sort_desc,
            )
        else:
            return self.comment_repository.find_all_by_dict(
                criteria=criteria,
                pagination=pagination,
                sort_by=sort_by,
                sort_desc=sort_desc,
            )

    def find_one(
        self,
        comment_id: PyObjectId,
        user_id: PyObjectId | None = None,
    ) -> CommentPublic:
        if user_id:
            comment = self.comment_repository.find_one_with_user_reaction(
                comment_id=comment_id, user_id=user_id
            )
        else:
            comment = self.comment_repository.find_one(comment_id)

        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comment with ID {comment_id} not found",
            )
        return comment

    def create_comment(
        self,
        user_id: PyObjectId,
        comment_data: CommentCreate,
        product_id: PyObjectId | None = None,
        parent_id: PyObjectId | None = None,
    ) -> CommentPublic:
        try:
            now = datetime.now(UTC)
            if parent_id:
                parent_comment = self.find_one(parent_id)
                comment = Comment(
                    user_id=user_id,
                    product_id=parent_comment.product_id,
                    parent_id=parent_id,
                    created_at=now,
                    **comment_data.model_dump(),
                )
            else:
                comment = Comment(
                    user_id=user_id,
                    product_id=product_id,
                    parent_id=parent_id,
                    created_at=now,
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
        parent_id: PyObjectId | None = None,
    ) -> CommentPublic:
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
