from centeral_marketplace.categories.core import Category
from centeral_marketplace.infrastructure.json import (
    PaginatedResponse,
    Pagination,
)
from centeral_marketplace.categories.service import CategoryService
from fastapi import APIRouter
from fastapi_injector import Injected

category_router = APIRouter(
    prefix="/category",
    tags=["category"],
)


@category_router.get("/", response_model=PaginatedResponse[Category])
async def get_categories(
    category_service: CategoryService = Injected(CategoryService),
):
   

    paginated = category_service.find_all()

    return paginated


