from typing import Optional, List, Dict
from centeral_marketplace.infrastructure.json import MongoBaseModel
from pydantic import Field


class Category(MongoBaseModel):
    category_name: str = Field(default="")
    parent_category: Optional[str] = Field(default=None)
    subcategories: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class CategoryMapping:
    """
    Hierarchical category mapping for the marketplace.
    Maps parent categories to their subcategories and provides lookup functionality.
    Now supports both database-driven and fallback hardcoded categories.
    """

    # Fallback hardcoded hierarchy (used if database is empty)
    FALLBACK_CATEGORY_HIERARCHY = {
        "technology": [
            "phones",
            "smartphones",
            "android",
            "iphone",
            "laptops",
            "gaming",
            "tablets",
            "wearables",
        ],
        "clothes": [
            "men",
            "women",
            "dresses",
            "shirts",
            "t-shirts",
            "jeans",
            "evening dresses",
        ],
        "shoes": ["men", "women", "formal", "casual", "oxford", "sneakers", "boots"],
        "accessories": [
            "bags",
            "backpacks",
            "laptop bags",
            "jewelry",
            "watches",
            "belts",
        ],
    }

    # Runtime hierarchy loaded from database
    _cached_hierarchy: Optional[Dict[str, List[str]]] = None

    @classmethod
    def set_hierarchy(cls, hierarchy: Dict[str, List[str]]):
        """Set the category hierarchy from database."""
        cls._cached_hierarchy = hierarchy

    @classmethod
    def get_hierarchy(cls) -> Dict[str, List[str]]:
        """Get the current category hierarchy (database or fallback)."""
        return (
            cls._cached_hierarchy
            if cls._cached_hierarchy
            else cls.FALLBACK_CATEGORY_HIERARCHY
        )

    @classmethod
    def get_parent_categories(cls) -> List[str]:
        """Get all parent category names."""
        return list(cls.get_hierarchy().keys())

    @classmethod
    def get_subcategories(cls, parent_category: str) -> List[str]:
        """Get subcategories for a given parent category."""
        return cls.get_hierarchy().get(parent_category.lower(), [])

    @classmethod
    def get_parent_category(cls, subcategory: str) -> Optional[str]:
        """Find the parent category for a given subcategory."""
        subcategory_lower = subcategory.lower()
        for parent, subcategories in cls.get_hierarchy().items():
            if subcategory_lower in [sub.lower() for sub in subcategories]:
                return parent
        return None

    @classmethod
    def get_all_subcategories(cls) -> List[str]:
        """Get all subcategories across all parent categories."""
        all_subcategories = []
        for subcategories in cls.get_hierarchy().values():
            all_subcategories.extend(subcategories)
        return all_subcategories

    @classmethod
    def expand_categories(cls, categories: List[str]) -> List[str]:
        """
        Expand categories to include both parent and child categories.
        If a parent category is provided, include all its subcategories.
        If a subcategory is provided, include it as-is.
        """
        expanded_categories = []

        for category in categories:
            category_lower = category.lower().strip()
            if not category_lower:
                continue

            # Check if it's a parent category
            hierarchy = cls.get_hierarchy()
            if category_lower in hierarchy:
                # Add the parent category
                expanded_categories.append(category_lower)
                # Add all its subcategories
                expanded_categories.extend(
                    [sub.lower() for sub in hierarchy[category_lower]]
                )
            else:
                # Check if it's a subcategory
                parent = cls.get_parent_category(category_lower)
                if parent:
                    # Add the subcategory
                    expanded_categories.append(category_lower)
                    # Optionally add the parent category for broader matching
                    expanded_categories.append(parent)
                else:
                    # Unknown category, add as-is for flexibility
                    expanded_categories.append(category_lower)

        # Remove duplicates while preserving order
        return list(dict.fromkeys(expanded_categories))

    @classmethod
    def is_valid_category(cls, category: str) -> bool:
        """Check if a category is valid (either parent or subcategory)."""
        category_lower = category.lower().strip()
        hierarchy = cls.get_hierarchy()
        return (
            category_lower in hierarchy
            or cls.get_parent_category(category_lower) is not None
        )
