from dataclasses import dataclass
import logging
import traceback
from typing import Optional
from datetime import datetime, UTC
from centeral_marketplace.reactions.core import Reaction, ReactionTarget, ReactionType
from centeral_marketplace.reactions.repository import ReactionRepository
from centeral_marketplace.products.repository import ProductRepository
from centeral_marketplace.comments.repository import CommentRepository
from fastapi import HTTPException, status
from injector import inject, singleton

from core import PyObjectId

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


@inject
@singleton
@dataclass
class ReactionService:
    reaction_repo: ReactionRepository
    product_repo: ProductRepository
    comment_repo: CommentRepository

    def react(
        self,
        user_id: PyObjectId,
        target_id: PyObjectId,
        target_type: ReactionTarget,
        reaction_type: ReactionType,
    ):
        try:
            existing = self.reaction_repo.find_one_by_user_and_target(user_id, target_id)

            if existing and existing.reaction_type == reaction_type:
                self.reaction_repo.delete(existing.id)
                self._adjust_target(target_id, target_type, reaction_type, decrement=True)
                return existing

            if existing:
                self._adjust_target(
                    target_id, target_type, existing.reaction_type, decrement=True
                )
                self.reaction_repo.delete(existing.id)

            now = datetime.now(UTC)
            reaction = Reaction(
                user_id=user_id,
                target_id=target_id,
                target_type=target_type,
                reaction_type=reaction_type,
                created_at=now,
            )

            self.reaction_repo.save(reaction)
            self._adjust_target(target_id, target_type, reaction_type, decrement=False)

            return reaction
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing reaction for target {target_id}: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to process reaction",
            ) from e

    def get_reaction(
        self, user_id: PyObjectId, target_id: PyObjectId
    ) -> Optional[Reaction]:
        try:
            return self.reaction_repo.find_one_by_user_and_target(user_id, target_id)
        except Exception as e:
            logger.error(f"Error getting reaction for target {target_id} by user {user_id}: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve reaction",
            ) from e

    def _adjust_target(self, target_id, target_type, reaction_type, decrement=False):
        try:
            delta = -1 if decrement else 1

            if target_type == ReactionTarget.PRODUCT:
                product = self.product_repo.find_one(target_id)
                if not product:
                    logger.error(f"Product with ID {target_id} not found for reaction adjustment")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, 
                        detail=f"Product with ID {target_id} not found"
                    )
                if reaction_type == ReactionType.UPVOTE:
                    product.upvotes += delta
                elif reaction_type == ReactionType.DOWNVOTE:
                    product.downvotes += delta
                self.product_repo.save(product)

            elif target_type == ReactionTarget.COMMENT:
                comment = self.comment_repo.find_one(target_id)
                if not comment:
                    logger.error(f"Comment with ID {target_id} not found for reaction adjustment")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, 
                        detail=f"Comment with ID {target_id} not found"
                    )
                if reaction_type == ReactionType.LIKE:
                    comment.likes += delta
                elif reaction_type == ReactionType.DISLIKE:
                    comment.dislikes += delta
                self.comment_repo.save(comment)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adjusting target {target_id} for reaction: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to update reaction count",
            ) from e
