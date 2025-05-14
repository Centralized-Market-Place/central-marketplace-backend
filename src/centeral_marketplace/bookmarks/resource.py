from typing import Annotated
from fastapi import APIRouter, Depends, status
from fastapi_injector import Injected

from centeral_marketplace.bookmarks.core import Bookmark
from centeral_marketplace.bookmarks.service import BookmarkService
from centeral_marketplace.infrastructure.json import PaginatedResponse, Pagination
from centeral_marketplace.users.core import User
from core import PyObjectId
from middleware import get_current_user

bookmark_router = APIRouter(
    prefix="/bookmarks",
    tags=["bookmarks"],
)


@bookmark_router.post(
    "/{product_id}", response_model=Bookmark, status_code=status.HTTP_201_CREATED
)
async def add_bookmark(
    product_id: PyObjectId,
    current_user: Annotated[User, Depends(get_current_user)],
    bookmark_service: BookmarkService = Injected(BookmarkService),
):
    return bookmark_service.add_bookmark(current_user.id, product_id)


@bookmark_router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_bookmark(
    product_id: PyObjectId,
    current_user: Annotated[User, Depends(get_current_user)],
    bookmark_service: BookmarkService = Injected(BookmarkService),
):
    bookmark_service.remove_bookmark(current_user.id, product_id)


@bookmark_router.get("/{product_id}", response_model=Bookmark)
async def get_bookmark(
    product_id: PyObjectId,
    current_user: Annotated[User, Depends(get_current_user)],
    bookmark_service: BookmarkService = Injected(BookmarkService),
):
    return bookmark_service.get_bookmark(current_user.id, product_id)


@bookmark_router.get("/", response_model=PaginatedResponse[Bookmark])
async def find_bookmarks(
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = 1,
    page_size: int = 20,
    sort_desc: bool = True,
    bookmark_service: BookmarkService = Injected(BookmarkService),
):
    pagination = Pagination(page=page, size=page_size)
    return bookmark_service.find_bookmarks(
        current_user.id, pagination=pagination, sort_desc=sort_desc
    )
