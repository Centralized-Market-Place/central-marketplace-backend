from centeral_marketplace.infrastructure.json import PaginatedResponse, Pagination, RestConverter
from centeral_marketplace.products.service import ProductService
from fastapi import APIRouter
from fastapi_injector import Injected


product_router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@product_router.get("/", response_model=PaginatedResponse)
async def get_products(
    page: int = 1,
    page_size: int = 20,
    sort_by: str = None,
    sort_desc: bool = True,
    query: str = None,
    channel_id: str = None, 
    product_service: ProductService = Injected(ProductService),
    converter: RestConverter = Injected(RestConverter),
):
    criteria = {}

    if query:
        criteria["$or"] = [
            {"name": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}},
        ]
    
    if channel_id:
        criteria["channelId"] = channel_id

    total = product_service.count_all_by_dict(criteria=criteria)
    products = list(
        product_service.find_all(
            pagination=Pagination(page=page, size=page_size),
            sort_by=sort_by,
            sort_desc=sort_desc,
            criteria=criteria,
        )
    )

    return  PaginatedResponse(
            page=page,
            page_size=page_size,
            total=total,
            items=converter.unstructure(products),
        )
 


@product_router.get("/{product_id}")
async def get_product(
    product_id: str,
    product_service: ProductService = Injected(ProductService),
    converter: RestConverter = Injected(RestConverter),
):
    product = product_service.find_one(product_id)
    return converter.unstructure(product)
