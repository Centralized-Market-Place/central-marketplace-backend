from dataclasses import dataclass
from typing import Iterator
from centeral_marketplace.infrastructure.json import Pagination
from centeral_marketplace.products.core import Product
from injector import inject, singleton
from centeral_marketplace.infrastructure.mongo import MongoDBJsonRepositoryDelegate
from centeral_marketplace.infrastructure.repository import RepositoryInterface
from config import Config


@inject
@singleton
@dataclass
class ProductRepository(RepositoryInterface[Product]):
    config: Config

    def __post_init__(self):
        self.delegate = MongoDBJsonRepositoryDelegate(
            collection_name="products", cls=Product, config=self.config
        )

    def close(self):
        self.delegate.close()

    def save(self, data: Product):
        return self.delegate.save(data)

    def save_all(self, data: list[Product]):
        return self.delegate.save_all(data)

    def find_all(
        self, sort_by: str = None, sort_desc: bool = True, pagination: Pagination = None
    ) -> Iterator[Product]:
        return self.delegate.find_all(
            pagination=pagination, sort_by=sort_by, sort_desc=sort_desc
        )

    def find_one(self, id: str):
        return self.delegate.find_one(id)

    def find_all_by(
        self,
        sort_by: str = None,
        sort_desc: bool = True,
        pagination: Pagination = None,
        **kwargs,
    ) -> Iterator[Product]:
        return self.delegate.find_all_by_dict(
            criteria=kwargs, pagination=pagination, sort_by=sort_by, sort_desc=sort_desc
        )

    def find_one_by_dict(self, criteria: dict) -> Product:
        return self.delegate.find_one_by_dict(criteria)

    def delete_one(self, id: str):
        return self.delegate.delete_one(id)

    def find_all_by_dict(
        self,
        criteria: dict,
        pagination=None,
        sort_by: str | None = None,
        sort_desc: bool = True,
    ) -> Iterator[Product]:
        return self.delegate.find_all_by_dict(
            criteria=criteria,
            pagination=pagination,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )

    def count_all_by_dict(self, criteria):
        return self.delegate.count_all_by_dict(criteria)

    def delete_all(self):
        return self.delegate.delete_all()
