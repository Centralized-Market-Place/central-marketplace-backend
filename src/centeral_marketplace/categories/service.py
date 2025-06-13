from dataclasses import dataclass
from centeral_marketplace.infrastructure.json import Pagination, PaginatedResponse
from centeral_marketplace.categories.core import Category
from centeral_marketplace.categories.repository import CategoryRepository
from centeral_marketplace.users.repository import UserRepository
from injector import inject, singleton

from core import PyObjectId


@singleton
@inject
@dataclass
class CategoryService:
    category_repository: CategoryRepository
    user_repository: UserRepository

    def find_all(
        self,
        criteria: dict = None,
    ) -> PaginatedResponse[Category]:
        if criteria is None:
            criteria = {}
        return self.category_repository.find_all_by_dict(
            criteria=criteria,
        )
