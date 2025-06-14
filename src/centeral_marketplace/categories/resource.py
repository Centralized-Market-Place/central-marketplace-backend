from typing import Dict, List
from centeral_marketplace.categories.core import Category
from centeral_marketplace.infrastructure.json import (
    PaginatedResponse,
    Pagination,
)
from centeral_marketplace.categories.service import CategoryService
from fastapi import APIRouter, Query
from fastapi_injector import Injected

category_router = APIRouter(
    prefix="/category",
    tags=["category"],
)


@category_router.get("/", response_model=PaginatedResponse[Category])
async def get_categories(
    category_service: CategoryService = Injected(CategoryService),
):
    """Get all categories from the database."""
    paginated = category_service.find_all()
    return paginated


@category_router.get("/hierarchy", response_model=Dict[str, List[str]])
async def get_category_hierarchy(
    category_service: CategoryService = Injected(CategoryService),
):
    """
    Get the complete category hierarchy with parent-child relationships.
    Returns a dictionary where keys are parent categories and values are lists of subcategories.
    """
    return category_service.get_category_hierarchy()

