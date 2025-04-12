from typing import Annotated
from centeral_marketplace.comments.core import Comment, CommentCreate, CommentUpdate
from centeral_marketplace.infrastructure.json import (
    PaginatedResponse,
    Pagination,
    RestConverter,
)
from centeral_marketplace.products.core import Product
from centeral_marketplace.products.service import ProductService
from centeral_marketplace.users.core import User
from fastapi import APIRouter, Depends, Query, status
from fastapi_injector import Injected
from middleware import get_current_user


product_router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@product_router.get("/", response_model=PaginatedResponse[Product])
async def get_products(
    page: int = 1,
    page_size: int = 20,
    sort_by: str = None,
    sort_desc: bool = True,
    query: str = None,
    channel_id: int = Query(None, alias="channelId"),
    product_service: ProductService = Injected(ProductService),
    converter: RestConverter = Injected(RestConverter),
):
    criteria = (
        {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
            ]
        }
        if query
        else {}
    )

    if channel_id:
        criteria["channel_id"] = channel_id

    return product_service.find_all(
        pagination=Pagination(page=page, size=page_size),
        sort_by=sort_by,
        sort_desc=sort_desc,
        criteria=criteria,
    )


@product_router.get("/{product_id}", response_model=Product)
async def get_product(
    product_id: str,
    product_service: ProductService = Injected(ProductService),
    converter: RestConverter = Injected(RestConverter),
):
    product = product_service.find_one(product_id)
    return converter.unstructure(product)


@product_router.get("/{product_id}/comments")
async def get_product_comments(
    product_id: str,
    product_service: ProductService = Injected(ProductService),
    page: int = 1,
    page_size: int = 20,
    sort_desc: bool = True,
    converter: RestConverter = Injected(RestConverter),
):
    pagination = Pagination(page=page, size=page_size)
    comments = product_service.find_all_comments(
        product_id=product_id,
        pagination=pagination,
        sort_desc=sort_desc,
    )
    return comments


@product_router.post("/{product_id}/comments", response_model=Comment)
async def post_product_comment(
    product_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    comment_data: CommentCreate,
    product_service: ProductService = Injected(ProductService),
    converter: RestConverter = Injected(RestConverter),
):
    comment = product_service.create_post_comment(
        user_id=current_user.id, product_id=product_id, comment_data=comment_data
    )
    return converter.unstructure(comment)


@product_router.post("/{product_id}/comments/{comment_id}", response_model=Comment)
async def update_product_comment(
    product_id: str,
    comment_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    comment_data: CommentUpdate,
    product_service: ProductService = Injected(ProductService),
    converter: RestConverter = Injected(RestConverter),
):
    comment = product_service.update_post_comment(
        user_id=current_user.id,
        product_id=product_id,
        comment_id=comment_id,
        comment_data=comment_data,
    )
    return converter.unstructure(comment)


@product_router.delete(
    "/{product_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_product_comment(
    product_id: str,
    comment_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    product_service: ProductService = Injected(ProductService),
):
    product_service.delete_post_comment(
        user_id=current_user.id, product_id=product_id, comment_id=comment_id
    )
