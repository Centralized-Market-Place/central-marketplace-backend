from dataclasses import dataclass
from typing import Dict, List
from centeral_marketplace.infrastructure.json import PaginatedResponse
from centeral_marketplace.categories.core import Category, CategoryMapping
from centeral_marketplace.categories.repository import CategoryRepository
from centeral_marketplace.users.repository import UserRepository
from injector import inject, singleton


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

    def get_category_hierarchy(self) -> Dict[str, List[str]]:
        """Get the complete category hierarchy with parent-child relationships."""
        self._ensure_hierarchy_loaded()
        return CategoryMapping.get_hierarchy()

    def _ensure_hierarchy_loaded(self):
        """Ensure category hierarchy is loaded from database."""
        if CategoryMapping._cached_hierarchy is None:
            self._load_hierarchy_from_database()

    def _load_hierarchy_from_database(self):
        """Load category hierarchy from database."""
        try:
            # Get all parent categories from database
            parent_categories = self.category_repository.find_all_by_dict(
                criteria={"parent_category": None}
            )

            if not parent_categories.items:
                # If no categories in database, seed with default data
                self.seed_default_categories()
                return

            # Build hierarchy from database
            hierarchy = {}
            for parent_cat in parent_categories.items:
                parent_name = parent_cat.category_name.lower()

                # Get subcategories for this parent
                subcategories = self.category_repository.find_all_by_dict(
                    criteria={"parent_category": parent_name}
                )

                hierarchy[parent_name] = [
                    sub.category_name.lower() for sub in subcategories.items
                ]

            # Set the loaded hierarchy
            CategoryMapping.set_hierarchy(hierarchy)

        except Exception as e:
            print(f"Error loading categories from database: {e}")
            # Fall back to hardcoded categories
            CategoryMapping.set_hierarchy(CategoryMapping.FALLBACK_CATEGORY_HIERARCHY)
