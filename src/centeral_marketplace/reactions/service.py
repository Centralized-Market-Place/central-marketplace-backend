from dataclasses import dataclass
from typing import Optional
from datetime import datetime, UTC
from centeral_marketplace.reactions.core import Reaction, ReactionTarget, ReactionType
from centeral_marketplace.reactions.repository import ReactionRepository
from centeral_marketplace.products.repository import ProductRepository
from centeral_marketplace.comments.repository import CommentRepository
from fastapi import HTTPException, status
from injector import inject, singleton

from core import PyObjectId


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

    def get_reaction(
        self, user_id: PyObjectId, target_id: PyObjectId
    ) -> Optional[Reaction]:
        return self.reaction_repo.find_one_by_user_and_target(user_id, target_id)

    def _adjust_target(self, target_id, target_type, reaction_type, decrement=False):
        delta = -1 if decrement else 1

        if target_type == ReactionTarget.PRODUCT:
            product = self.product_repo.find_one(target_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
                )
            if reaction_type == ReactionType.UPVOTE:
                product.upvotes += delta
            elif reaction_type == ReactionType.DOWNVOTE:
                product.downvotes += delta
            self.product_repo.save(product)

        elif target_type == ReactionTarget.COMMENT:
            comment = self.comment_repo.find_one(target_id)
            if not comment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
                )
            if reaction_type == ReactionType.LIKE:
                comment.likes += delta
            elif reaction_type == ReactionType.DISLIKE:
                comment.dislikes += delta
            self.comment_repo.save(comment)
