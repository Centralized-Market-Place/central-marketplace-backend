from fastapi import APIRouter, Depends
from fastapi_injector import Injected
from typing import Annotated
from centeral_marketplace.reactions.core import ReactionTarget, ReactionType
from centeral_marketplace.reactions.service import ReactionService
from centeral_marketplace.users.core import User
from middleware import get_current_user

reaction_router = APIRouter(
    prefix="/reactions",
    tags=["reactions"],
)


@reaction_router.post("/{target_type}/{target_id}")
async def react_to_target(
    target_type: ReactionTarget,
    target_id: str,
    reaction_type: ReactionType,
    current_user: Annotated[User, Depends(get_current_user)],
    reaction_service: ReactionService = Injected(ReactionService),
):
    return reaction_service.react(
        user_id=current_user.id,
        target_id=target_id,
        target_type=target_type,
        reaction_type=reaction_type,
    )
