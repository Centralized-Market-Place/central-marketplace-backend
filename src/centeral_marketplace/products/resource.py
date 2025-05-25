from typing import Annotated, Optional, List

from centeral_marketplace.comments.core import (
    CommentCreate,
    CommentPublic,
    CommentUpdate,
)
from centeral_marketplace.infrastructure.json import (
    PaginatedResponse,
    Pagination,
)
from centeral_marketplace.products.core import ProductPublic, UpdateProduct
from centeral_marketplace.products.service import ProductService
from centeral_marketplace.users.core import User
from fastapi import APIRouter, Depends, status
from fastapi_injector import Injected

from core import PyObjectId
from middleware import get_current_user, get_current_user_optional


product_router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@product_router.get("/", response_model=PaginatedResponse[ProductPublic])
async def get_products(
    current_user: Annotated[User, Depends(get_current_user_optional)],
    page: int = 1,
    page_size: int = 20,
    sort_by: str = None,
    sort_desc: bool = True,
    query: str = None,
    channel_id: PyObjectId = Query(None, alias="channelId"),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    categories: List[str] = Query(default=[]),
    location: Optional[str] = Query(None),
    channel_id: PyObjectId = None,
    product_service: ProductService = Injected(ProductService),
):
    criteria: dict = {}

    # Search by query (name or description)
    if query:
        criteria["$or"] = [
            {"name": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}},
        ]

    # Filter by channel
        criteria["$text"] = {"$search": query}
    if channel_id:
        criteria["channel_id"] = channel_id

    # Filter by price range
    if min_price is not None or max_price is not None:
        criteria["price"] = {}
        if min_price is not None:
            criteria["price"]["$gte"] = min_price
        if max_price is not None:
            criteria["price"]["$lte"] = max_price

    # Normalize category list
    normalized_category = []
    if isinstance(categories, list):
        normalized_category = [cat.lower() for cat in categories]
    elif isinstance(categories, str):
        normalized_category = [categories.lower()]

    if normalized_category:
        criteria["categories"] = {"$in": normalized_category}

    # Filter by exact location (case-insensitive match)
    if location:
        criteria["location"] = {"$regex": f"^{location}$", "$options": "i"}

    user_id = current_user.id if current_user else None

    return product_service.find_all(
        user_id=user_id,
        pagination=Pagination(page=page, size=page_size),
        sort_by=sort_by,
        sort_desc=sort_desc,
        criteria=criteria,
    )


@product_router.get("/bookmarked", response_model=PaginatedResponse[ProductPublic])
async def get_product_bookmarks(
    current_user: Annotated[User, Depends(get_current_user)],
    product_service: ProductService = Injected(ProductService),
    page: int = 1,
    page_size: int = 20,
    sort_desc: bool = True,
    sort_by: str = "created_at",
    query: str = None,
):
    pagination = Pagination(page=page, size=page_size)
    return product_service.find_bookmarked_products(
        user_id=current_user.id,
        pagination=pagination,
        sort_desc=sort_desc,
        sort_by=sort_by,
        query=query,
    )


@product_router.get("/{product_id}", response_model=ProductPublic)
async def get_product(
    current_user: Annotated[User, Depends(get_current_user_optional)],
    product_id: PyObjectId,
    product_service: ProductService = Injected(ProductService),
):
    user_id = current_user.id if current_user else None
    return product_service.find_one(product_id, user_id=user_id)


@product_router.get(
    "/{product_id}/comments", response_model=PaginatedResponse[CommentPublic]
)
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


@product_router.post("/{product_id}/comments", response_model=CommentPublic)
async def post_product_comment(
    product_id: PyObjectId,
    current_user: Annotated[User, Depends(get_current_user)],
    comment_data: CommentCreate,
    product_service: ProductService = Injected(ProductService),
):
    return product_service.create_post_comment(
        user_id=current_user.id, product_id=product_id, comment_data=comment_data
    )


@product_router.post(
    "/{product_id}/comments/{comment_id}", response_model=CommentPublic
)
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


@product_router.post("/{product_id}/share", response_model=ProductPublic)
async def increment_product_share_count(
    product_id: PyObjectId,
    current_user: Annotated[User, Depends(get_current_user)],
    product_service: ProductService = Injected(ProductService),
):
    return product_service.increment_share_count(
        product_id=product_id, user_id=current_user.id
    )

@product_router.post("/{product_id}", response_model=ProductPublic)
async def update_product(
    product_id: PyObjectId,
    product_update: UpdateProduct,
    current_user: Annotated[User, Depends(get_current_user)],
    product_service: ProductService = Injected(ProductService),
): 
    
    return product_service.update_product(product_id,product_update, current_user)

@product_router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: PyObjectId,
    current_user: Annotated[User, Depends(get_current_user)],
    product_service: ProductService = Injected(ProductService),
):
    return product_service.delete_product(product_id, current_user)
