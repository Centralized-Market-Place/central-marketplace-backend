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


@category_router.get("/all", response_model=List[str])
async def get_all_categories(
    category_service: CategoryService = Injected(CategoryService),
):
    """Get all categories (parents and subcategories) as a flat list."""
    return category_service.get_all_categories_flat()


@category_router.get("/validate", response_model=Dict[str, List[str]])
async def validate_categories(
    categories: List[str] = Query(..., description="List of categories to validate"),
    category_service: CategoryService = Injected(CategoryService),
):
    """
    Validate a list of categories and categorize them as valid/invalid, parent/subcategory.
    Returns validation results with categorized lists.
    """
    return category_service.validate_categories(categories)


@category_router.post("/refresh")
async def refresh_categories(
    category_service: CategoryService = Injected(CategoryService),
):
    """
    Refresh the category hierarchy from the database.
    Forces a reload of categories from the database.
    """
    try:
        # Clear the cache to force reload
        from centeral_marketplace.categories.core import CategoryMapping
        CategoryMapping._cached_hierarchy = None
        
        # Force reload from database
        hierarchy = category_service.get_category_hierarchy()
        
        return {
            "message": "Categories refreshed successfully", 
            "status": "success",
            "hierarchy": hierarchy
        }
    except Exception as e:
        return {"message": f"Error refreshing categories: {str(e)}", "status": "error"}


