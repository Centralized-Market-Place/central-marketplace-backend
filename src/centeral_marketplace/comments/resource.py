from typing import Annotated, Optional
from centeral_marketplace.comments.core import (
    CommentCreate,
    CommentUpdate,
    CommentPublic,
)
from centeral_marketplace.comments.service import CommentService
from centeral_marketplace.infrastructure.json import Pagination, PaginatedResponse
from centeral_marketplace.users.core import User
from fastapi import APIRouter, Depends, status
from fastapi_injector import Injected

from core import PyObjectId
from middleware import get_current_user, get_current_user_optional


comment_router = APIRouter(
    prefix="/comments",
    tags=["comments"],
)


@comment_router.get("/{comment_id}", response_model=CommentPublic)
async def get_comment(
    comment_id: PyObjectId,
    current_user: Annotated[Optional[User], Depends(get_current_user_optional)],
    comment_service: CommentService = Injected(CommentService),
):
    return comment_service.find_one(
        comment_id=comment_id,
        user_id=(current_user.id if current_user else None),
    )


@comment_router.get(
    "/{comment_id}/replies", response_model=PaginatedResponse[CommentPublic]
)
async def get_comment_replies(
    comment_id: PyObjectId,
    current_user: Annotated[Optional[User], Depends(get_current_user_optional)],
    comment_service: CommentService = Injected(CommentService),
    page: int = 1,
    page_size: int = 20,
    sort_desc: bool = True,
):
    criteria = {"parent_id": comment_id}
    pagination = Pagination(page=page, size=page_size)
    return comment_service.find_all(
        criteria=criteria,
        pagination=pagination,
        sort_by="created_at",
        sort_desc=sort_desc,
        user_id=(current_user.id if current_user else None),
    )


@comment_router.post("/{comment_id}/replies", response_model=CommentPublic)
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


@comment_router.post("/{comment_id}/replies/{reply_id}", response_model=CommentPublic)
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
