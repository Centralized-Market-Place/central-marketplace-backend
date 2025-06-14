from dataclasses import dataclass
from injector import inject, singleton

from centeral_marketplace.infrastructure.json import PaginatedResponse
from centeral_marketplace.infrastructure.mongo import MongoDBJsonRepositoryDelegate
from centeral_marketplace.infrastructure.repository import RepositoryInterface
from centeral_marketplace.categories.core import Category
from config import Config
from core import PyObjectId


@inject
@singleton
@dataclass
class CategoryRepository(RepositoryInterface[Category]):
    config: Config

    def __post_init__(self):
        self.delegate = MongoDBJsonRepositoryDelegate(
            collection_name="categories", model=Category, config=self.config
        )
        self.delegate.ensure_index(
            "category_name", unique=True, name="categories_name_unique"
        )
        self.delegate.ensure_index("parent_category", name="categories_parent_category")

    def save(self, data: Category):
        return self.delegate.save(data)

    def save_all(self, data: list[Category]):
        return self.delegate.save_all(data)

    def find_all(self, sort_by: str = None, sort_desc: bool = True, pagination=None):
        return self.delegate.find_all(
            pagination=pagination, sort_by=sort_by, sort_desc=sort_desc
        )

    def find_one(self, id: PyObjectId):
        return self.delegate.find_one(id)

    def find_all_by(
        self,
        sort_by: str = None,
        sort_desc: bool = True,
        pagination=None,
        **kwargs,
    ):
        return self.delegate.find_all_by_dict(
            criteria=kwargs, pagination=pagination, sort_by=sort_by, sort_desc=sort_desc
        )

    def find_one_by_dict(self, criteria: dict):
        return self.delegate.find_one_by_dict(criteria)

    def delete_one(self, id: PyObjectId):
        return self.delegate.delete_one(id)

    def find_all_by_dict(
        self,
        criteria: dict,
        pagination=None,
        sort_by: str | None = None,
        sort_desc: bool = True,
    ) -> PaginatedResponse[Category]:
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
