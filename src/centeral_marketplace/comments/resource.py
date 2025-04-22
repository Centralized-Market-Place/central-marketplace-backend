from typing import Annotated
from centeral_marketplace.comments.core import Comment, CommentCreate, CommentUpdate
from centeral_marketplace.comments.service import CommentService
from centeral_marketplace.infrastructure.json import Pagination
from centeral_marketplace.users.core import User
from fastapi import APIRouter, Depends, status
from fastapi_injector import Injected

from core import PyObjectId
from middleware import get_current_user


comment_router = APIRouter(
    prefix="/comments",
    tags=["comments"],
)


@comment_router.get("/{comment_id}", response_model=Comment)
async def get_comment(
    comment_id: PyObjectId,
    comment_service: CommentService = Injected(CommentService),
):
    return comment_service.find_one(comment_id)


@comment_router.get("/{comment_id}/replies")
async def get_comment_replies(
    comment_id: str,
    comment_service: CommentService = Injected(CommentService),
    page: int = 1,
    page_size: int = 20,
    sort_desc: bool = True,
):
    criteria = {"parent_id": comment_id}
    pagination = Pagination(page=page, size=page_size)
    comments = comment_service.find_all(
        criteria=criteria, pagination=pagination, sort_desc=sort_desc
    )
    return comments


@comment_router.post("/{comment_id}/replies", response_model=Comment)
async def post_comment_reply(
    comment_id: PyObjectId,
    comment_data: CommentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    comment_service: CommentService = Injected(CommentService),
):
    comment = comment_service.create_comment(
        user_id=current_user.id, parent_id=comment_id, comment_data=comment_data
    )
    return comment


@comment_router.post("/{comment_id}/replies/{reply_id}", response_model=Comment)
async def update_comment_reply(
    comment_id: PyObjectId,
    reply_id: PyObjectId,
    comment_data: CommentUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    comment_service: CommentService = Injected(CommentService),
):
    comment = comment_service.update_comment(
        user_id=current_user.id,
        comment_id=reply_id,
        parent_id=comment_id,
        comment_data=comment_data,
    )
    return comment


@comment_router.delete(
    "/{comment_id}/replies/{reply_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_comment_reply(
    comment_id: PyObjectId,
    reply_id: PyObjectId,
    current_user: Annotated[User, Depends(get_current_user)],
    comment_service: CommentService = Injected(CommentService),
):
    comment_service.find_one(comment_id=comment_id)
    comment_service.delete_comment(user_id=current_user.id, comment_id=reply_id)
