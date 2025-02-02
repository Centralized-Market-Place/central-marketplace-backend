from dataclasses import dataclass
from centeral_marketplace.infrastructure.json import Pagination
from centeral_marketplace.products.core import Product
from centeral_marketplace.products.repository import ProductRepository
from injector import inject, singleton


@singleton
@inject
@dataclass
class ProductService:
    product_repository: ProductRepository

    def find_all(
        self,
        pagination: Pagination = None,
        sort_by: str = None,
        sort_desc: bool = True,
        criteria: dict = {},
    ) -> list[Product]:
        
        return self.product_repository.find_all_by_dict(
            pagination=pagination,
            sort_by=sort_by,
            sort_desc=sort_desc,
            criteria=criteria,
        )

    def count_all_by_dict(self, criteria: dict) -> int:
        return self.product_repository.count_all_by_dict(criteria)
