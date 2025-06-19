from dataclasses import dataclass
from centeral_marketplace.infrastructure.json import PaginatedResponse, Pagination
from centeral_marketplace.products.core import Product, ProductPublic
from centeral_marketplace.products.semantic_search import get_semantic_search_service
from centeral_marketplace.products.pipeline_builder import ProductPipelineBuilder
from centeral_marketplace.reactions.core import ReactionTarget
from injector import inject, singleton
from centeral_marketplace.infrastructure.mongo import MongoDBJsonRepositoryDelegate
from centeral_marketplace.infrastructure.repository import RepositoryInterface
from config import Config
from core import PyObjectId
from bson import ObjectId
from typing import Optional
import logging

logger = logging.getLogger(__name__)

@inject
@singleton
@dataclass
class ProductRepository(RepositoryInterface[Product]):
    config: Config

    def __post_init__(self):
        self.delegate = MongoDBJsonRepositoryDelegate(
            collection_name="structured_products", model=Product, config=self.config
        )
        
        self.semantic_search_service = get_semantic_search_service()

        self.delegate.ensure_text_index(
            ["name", "description"], name="products_text_search"
        )
        self.delegate.ensure_index("date", name="products_date")
        self.delegate.ensure_index("price", name="products_price")
        self.delegate.ensure_index("is_available", name="products_is_available")
        self.delegate.ensure_index("is_deleted", name="products_is_deleted")
        self.delegate.ensure_index("channel_id", name="products_channel_id")
        self.delegate.ensure_index("categories", name="products_categories")

    def save(self, data: Product):
        return self.delegate.save(data)

    def save_all(self, data: list[Product]):
        return self.delegate.save_all(data)

    def _execute_pipeline_with_pagination(self, pipeline: list, page: int = 1, size: int = 0) -> tuple:
        result = list(self.delegate.collection.aggregate(pipeline))[0]
        items = [ProductPublic.model_validate(doc) for doc in result["items"]]
        total = result["total"][0]["count"] if result["total"] else 0
        return items, total

    def _should_use_semantic_search(self, query: str) -> bool:
        return (
            query and 
            query.strip() and 
            self.semantic_search_service.is_available and
            len(query.strip().split()) > 1
        )

    def find_all_with_user_reaction(
        self,
        user_id: PyObjectId,
        query: str = None,
        last_id: Optional[PyObjectId] = None,
        pagination: Pagination | None = None,
        sort_by: str = None,
        sort_desc: bool = True,
        criteria: dict | None = None,
    ) -> PaginatedResponse[ProductPublic]:
        if criteria is None:
            criteria = {}
        
        criteria["is_deleted"] = {"$ne": True}

        if last_id:
            criteria["_id"] = {"$gt": ObjectId(str(last_id))}

        page, size = (pagination.page, pagination.size) if pagination else (1, 0)

        builder = ProductPipelineBuilder()

        if self._should_use_semantic_search(query):
            query_vector = self.semantic_search_service.encode_query(query)
            if query_vector:
                builder.add_semantic_search(query_vector)
                builder.add_search_score()
                criteria.pop("$text", None)
        elif query:
            criteria = ProductPipelineBuilder.create_text_search_criteria(query, criteria)

        pipeline = (builder
                   .match_criteria(criteria)
                   .lookup_channel()
                   .sort_by(sort_by, sort_desc) if sort_by else builder)

        facet_stage = {
            "$facet": {
                "items": [
                    {
                        "$lookup": {
                            "from": "reactions",
                            "let": {"pid": "$_id"},
                            "pipeline": [
                                {
                                    "$match": {
                                        "$expr": {
                                            "$and": [
                                                {"$eq": ["$target_id", "$$pid"]},
                                                {"$eq": ["$user_id", ObjectId(str(user_id))]},
                                                {"$eq": ["$target_type", ReactionTarget.PRODUCT.value]},
                                            ]
                                        }
                                    }
                                },
                                {"$project": {"reaction_type": 1, "_id": 0}},
                            ],
                            "as": "userReaction",
                        }
                    },
                    {
                        "$addFields": {
                            "user_reaction": {
                                "$arrayElemAt": ["$userReaction.reaction_type", 0]
                            }
                        }
                    },
                    {"$project": {"userReaction": 0}},
                ],
                "total": [{"$count": "count"}],
            }
        }

        if pagination and size > 0:
            skip = (page - 1) * size
            facet_stage["$facet"]["items"].extend([
                {"$skip": skip},
                {"$limit": size}
            ])

        pipeline.pipeline.append(facet_stage)
        
        items, total = self._execute_pipeline_with_pagination(pipeline.build(), page, size)

        return PaginatedResponse(
            page=page,
            page_size=size,
            total=total,
            items=items,
        )

    def find_one_with_user_reaction(
        self,
        product_id: PyObjectId,
        user_id: PyObjectId,
    ) -> ProductPublic | None:
        criteria = {"_id": ObjectId(str(product_id))}
        criteria.update(ProductPipelineBuilder.base_product_criteria())
        
        builder = ProductPipelineBuilder()
        pipeline = (builder
                   .match_criteria(criteria)
                   .lookup_channel()
                   .lookup_user_reactions(user_id))

        docs = list(self.delegate.collection.aggregate(pipeline.build()))
        if not docs:
            return None
        return ProductPublic.model_validate(docs[0])

    def find_all(
        self, 
        query: str = None,
        sort_by: str = None, 
        sort_desc: bool = True, 
        pagination: Pagination = None
    ) -> PaginatedResponse[ProductPublic]:
        criteria = ProductPipelineBuilder.base_product_criteria()
        page, size = (pagination.page, pagination.size) if pagination else (1, 0)

        builder = ProductPipelineBuilder()

        if self._should_use_semantic_search(query):
            query_vector = self.semantic_search_service.encode_query(query)
            if query_vector:
                builder.add_semantic_search(query_vector)
                builder.add_search_score()
        elif query:
            criteria = ProductPipelineBuilder.create_text_search_criteria(query, criteria)

        pipeline = (builder
                   .match_criteria(criteria)
                   .lookup_channel())

        if sort_by:
            pipeline.sort_by(sort_by, sort_desc)

        pipeline.create_facet_with_pagination(page, size)
        
        items, total = self._execute_pipeline_with_pagination(pipeline.build(), page, size)

        return PaginatedResponse(
            page=page,
            page_size=size,
            total=total,
            items=items,
        )

    def find_one_product(self, id: PyObjectId) -> Product:
        criteria = {"_id": ObjectId(str(id)), "is_deleted": {"$ne": True}}
        return self.delegate.find_one_by_dict(criteria)

    def find_one(self, id: PyObjectId) -> ProductPublic | None:
        criteria = {"_id": ObjectId(str(id))}
        criteria.update(ProductPipelineBuilder.base_product_criteria())
        
        builder = ProductPipelineBuilder()
        pipeline = (builder
                   .match_criteria(criteria)
                   .lookup_channel())

        docs = list(self.delegate.collection.aggregate(pipeline.build()))
        if not docs:
            return None
        return ProductPublic.model_validate(docs[0])

    def find_bookmarked_with_query(
        self,
        user_id: PyObjectId,
        query: str | None = None,
        last_id: Optional[PyObjectId] = None,
        pagination: Pagination | None = None,
        sort_by: str | None = None,
        sort_desc: bool = True,
    ) -> PaginatedResponse[ProductPublic]:
        criteria = ProductPipelineBuilder.base_product_criteria()
        if last_id:
            criteria["_id"] = {"$gt": ObjectId(str(last_id))}

        page, size = (pagination.page, pagination.size) if pagination else (1, 0)

        builder = ProductPipelineBuilder()

        if self._should_use_semantic_search(query):
            query_vector = self.semantic_search_service.encode_query(query)
            if query_vector:
                builder.add_semantic_search(query_vector)
                builder.add_search_score()
        elif query:
            criteria = ProductPipelineBuilder.create_text_search_criteria(query, criteria)

        pipeline = (builder
                   .match_criteria(criteria)
                   .lookup_bookmarks(user_id)
                   .lookup_channel()
                   .unwind_channel())

        if sort_by:
            pipeline.sort_by(sort_by, sort_desc)
        else:
            pipeline.sort_by("_id", sort_desc)

        pipeline.create_facet_with_pagination(page, size)
        
        items, total = self._execute_pipeline_with_pagination(pipeline.build(), page, size)

        return PaginatedResponse(
            page=page,
            page_size=size,
            total=total,
            items=items,
        )

    def find_all_by(
        self,
        query: str = None,
        sort_by: str = None,
        sort_desc: bool = True,
        pagination: Pagination = None,
        **kwargs,
    ) -> PaginatedResponse[ProductPublic]:
        kwargs.update(ProductPipelineBuilder.base_product_criteria())
        page, size = (pagination.page, pagination.size) if pagination else (1, 0)

        builder = ProductPipelineBuilder()

        if self._should_use_semantic_search(query):
            query_vector = self.semantic_search_service.encode_query(query)
            if query_vector:
                builder.add_semantic_search(query_vector)
                builder.add_search_score()
        elif query:
            kwargs = ProductPipelineBuilder.create_text_search_criteria(query, kwargs)

        pipeline = (builder
                   .match_criteria(kwargs)
                   .lookup_channel())

        if sort_by:
            pipeline.sort_by(sort_by, sort_desc)

        pipeline.create_facet_with_pagination(page, size)
        
        items, total = self._execute_pipeline_with_pagination(pipeline.build(), page, size)

        return PaginatedResponse(
            page=page,
            page_size=size,
            total=total,
            items=items,
        )

    def find_one_by_dict(self, criteria: dict) -> ProductPublic | None:
        criteria.update(ProductPipelineBuilder.base_product_criteria())
        
        builder = ProductPipelineBuilder()
        pipeline = (builder
                   .match_criteria(criteria)
                   .lookup_channel())

        docs = list(self.delegate.collection.aggregate(pipeline.build()))
        if not docs:
            return None
        return ProductPublic.model_validate(docs[0])

    def delete_one(self, id: PyObjectId):
        return self.delegate.delete_one(id)

    def find_all_by_dict(
        self,
        criteria: dict,
        query: str = None,
        pagination: Pagination | None = None,
        sort_by: str | None = None,
        sort_desc: bool = True,
    ) -> PaginatedResponse[ProductPublic]:
        criteria = dict(criteria)  # Make a copy
        criteria.update(ProductPipelineBuilder.base_product_criteria())
        
        page, size = (pagination.page, pagination.size) if pagination else (1, 0)

        builder = ProductPipelineBuilder()

        if self._should_use_semantic_search(query):
            query_vector = self.semantic_search_service.encode_query(query)
            if query_vector:
                builder.add_semantic_search(query_vector)
                builder.add_search_score()
        elif query:
            criteria = ProductPipelineBuilder.create_text_search_criteria(query, criteria)

        pipeline = (builder
                   .match_criteria(criteria)
                   .lookup_channel())

        if sort_by:
            pipeline.sort_by(sort_by, sort_desc)

        pipeline.create_facet_with_pagination(page, size)
        
        items, total = self._execute_pipeline_with_pagination(pipeline.build(), page, size)

        return PaginatedResponse(
            page=page,
            page_size=size,
            total=total,
            items=items,
        )

    def count_all_by_dict(self, criteria):
        criteria = dict(criteria)
        criteria.update(ProductPipelineBuilder.base_product_criteria())
        
        builder = ProductPipelineBuilder()
        pipeline = (builder
                   .match_criteria(criteria)
                   .lookup_channel())
        
        pipeline.pipeline.append({"$count": "count"})
        
        result = list(self.delegate.collection.aggregate(pipeline.build()))
        return result[0]["count"] if result else 0

    def delete_all(self):
        return self.delegate.delete_all()

    def get_channel_analytics(self, channel_id: PyObjectId) -> dict:
        criteria = {"channel_id": ObjectId(str(channel_id))}
        criteria["is_deleted"] = {"$ne": True}
        pipeline = [
            {"$match": criteria},
            {
                "$group": {
                    "_id": None,
                    "total_products": {"$sum": 1},
                    "total_views": {"$sum": "$views"},
                    "average_price": {"$avg": "$price"},
                    "available_products": {
                        "$sum": {"$cond": [{"$eq": ["$is_available", True]}, 1, 0]}
                    },
                    "prices": {"$push": "$price"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "total_products": 1,
                    "total_views": 1,
                    "average_price": {"$ifNull": ["$average_price", 0]},
                    "available_products": 1,
                }
            },
        ]

        result = list(self.delegate.collection.aggregate(pipeline))
        if not result:
            return {
                "total_products": 0,
                "total_views": 0,
                "average_price": 0.0,
                "available_products": 0,
            }

        analytics = result[0]
        analytics["average_price"] = (
            float(analytics["average_price"]) if analytics["average_price"] else 0.0
        )

        return analytics
