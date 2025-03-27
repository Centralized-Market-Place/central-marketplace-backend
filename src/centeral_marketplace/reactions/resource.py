from fastapi import APIRouter, Depends
from fastapi_injector import Injected
from typing import Annotated, Optional
from centeral_marketplace.reactions.core import (
    CreateReaction,
    Reaction,
)
from centeral_marketplace.reactions.service import ReactionService
from centeral_marketplace.users.core import User
from middleware import get_current_user

reaction_router = APIRouter(
    prefix="/reactions",
    tags=["reactions"],
)


@reaction_router.post("/", response_model=Reaction)
async def react_to_target(
    react_data: CreateReaction,
    current_user: Annotated[User, Depends(get_current_user)],
    reaction_service: ReactionService = Injected(ReactionService),
):
    return reaction_service.react(
        user_id=current_user.id,
        target_id=react_data.target_id,
        target_type=react_data.target_type,
        reaction_type=react_data.reaction_type,
    )

@reaction_router.get("/{target_id}", response_model=Optional[Reaction])
async def get_reaction(
    target_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    reaction_service: ReactionService = Injected(ReactionService),
):
    reaction =  reaction_service.get_reaction(
        user_id=current_user.id,
        target_id=target_id,
    )
    if reaction is not None:
        return reaction

