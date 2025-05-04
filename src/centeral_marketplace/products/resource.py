from typing import Annotated
from centeral_marketplace.comments.core import Comment, CommentCreate, CommentUpdate
from centeral_marketplace.infrastructure.json import (
    PaginatedResponse,
    Pagination,
)
from centeral_marketplace.products.core import Product
from centeral_marketplace.products.service import ProductService
from centeral_marketplace.users.core import User
from fastapi import APIRouter, Depends, Query, status
from fastapi_injector import Injected

from core import PyObjectId
from middleware import get_current_user, get_current_user_optional


product_router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@product_router.get("/", response_model=PaginatedResponse[Product])
async def get_products(
    current_user: Annotated[User, Depends(get_current_user_optional)],
    page: int = 1,
    page_size: int = 20,
    sort_by: str = None,
    sort_desc: bool = True,
    query: str = None,
    channel_id: PyObjectId = Query(None, alias="channelId"),
    product_service: ProductService = Injected(ProductService),
):
    criteria: dict = {}
    if query:
        criteria["$or"] = [
            {"name": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}},
        ]
    if channel_id:
        criteria["channel_id"] = channel_id

    user_id = current_user.id if current_user else None

    return product_service.find_all(
        user_id=user_id,
        pagination=Pagination(page=page, size=page_size),
        sort_by=sort_by,
        sort_desc=sort_desc,
        criteria=criteria,
    )


@product_router.get("/{product_id}", response_model=Product)
async def get_product(
    current_user: Annotated[User, Depends(get_current_user_optional)],
    product_id: PyObjectId,
    product_service: ProductService = Injected(ProductService),
):
    user_id = current_user.id if current_user else None
    return product_service.find_one(product_id, user_id=user_id)


@product_router.get("/{product_id}/comments", response_model=PaginatedResponse[Comment])
async def get_product_comments(
    product_id: PyObjectId,
    current_user: Annotated[User, Depends(get_current_user_optional)],
    product_service: ProductService = Injected(ProductService),
    page: int = 1,
    page_size: int = 20,
    sort_desc: bool = True,
):
    pagination = Pagination(page=page, size=page_size)
    comments = product_service.find_all_comments(
        product_id=product_id,
        pagination=pagination,
        sort_desc=sort_desc,
        user_id=current_user.id if current_user else None,
    )
    return comments


@product_router.post("/{product_id}/comments", response_model=Comment)
async def post_product_comment(
    product_id: PyObjectId,
    current_user: Annotated[User, Depends(get_current_user)],
    comment_data: CommentCreate,
    product_service: ProductService = Injected(ProductService),
):
    return product_service.create_post_comment(
        user_id=current_user.id, product_id=product_id, comment_data=comment_data
    )


@product_router.post("/{product_id}/comments/{comment_id}", response_model=Comment)
async def update_product_comment(
    product_id: PyObjectId,
    comment_id: PyObjectId,
    current_user: Annotated[User, Depends(get_current_user)],
    comment_data: CommentUpdate,
    product_service: ProductService = Injected(ProductService),
):
    return product_service.update_post_comment(
        user_id=current_user.id,
        product_id=product_id,
        comment_id=comment_id,
        comment_data=comment_data,
    )


@product_router.delete(
    "/{product_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_product_comment(
    product_id: PyObjectId,
    comment_id: PyObjectId,
    current_user: Annotated[User, Depends(get_current_user)],
    product_service: ProductService = Injected(ProductService),
):
    product_service.delete_post_comment(
        user_id=current_user.id, product_id=product_id, comment_id=comment_id
    )
