from dataclasses import dataclass
from centeral_marketplace.infrastructure.json import PaginatedResponse, Pagination
from centeral_marketplace.products.core import Product, ProductPublic
from centeral_marketplace.reactions.core import ReactionTarget
from injector import inject, singleton
from centeral_marketplace.infrastructure.mongo import MongoDBJsonRepositoryDelegate
from centeral_marketplace.infrastructure.repository import RepositoryInterface
from config import Config
from core import PyObjectId
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING


@inject
@singleton
@dataclass
class ProductRepository(RepositoryInterface[Product]):
    config: Config

    def __post_init__(self):
        self.delegate = MongoDBJsonRepositoryDelegate(
            collection_name="products", model=Product, config=self.config
        )

    def save(self, data: Product):
        return self.delegate.save(data)

    def save_all(self, data: list[Product]):
        return self.delegate.save_all(data)

    def find_all_with_user_reaction(
        self,
        user_id: PyObjectId,
        pagination: Pagination | None = None,
        sort_by: str = None,
        sort_desc: bool = True,
        criteria: dict = None,
    ) -> PaginatedResponse[ProductPublic]:
        criteria = criteria or {}
        page, size = (pagination.page, pagination.size) if pagination else (1, 0)
        skip = (page - 1) * size

        pipeline = []
        pipeline.append({"$match": criteria})

        if sort_by:
            order = DESCENDING if sort_desc else ASCENDING
            pipeline.append({"$sort": {sort_by: order}})

        if pagination:
            pipeline.append({"$skip": skip})
            pipeline.append({"$limit": size})

        pipeline.append(
            {
                "$lookup": {
                    "from": "channels",
                    "localField": "channel_id",
                    "foreignField": "_id",
                    "as": "channel",
                }
            }
        )
        
        pipeline.append(
            {
                "$addFields": {
                    "channel": {
                        "$arrayElemAt": ["$channel", 0]
                    }
                }
            }
        )

        pipeline.append(
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
                                        {
                                            "$eq": [
                                                "$target_type",
                                                ReactionTarget.PRODUCT.value,
                                            ]
                                        },
                                    ]
                                }
                            }
                        },
                        {"$project": {"reaction_type": 1, "_id": 0}},
                    ],
                    "as": "userReaction",
                }
            }
        )

        pipeline.append(
            {
                "$addFields": {
                    "user_reaction": {
                        "$arrayElemAt": ["$userReaction.reaction_type", 0]
                    }
                }
            }
        )
        pipeline.append({"$project": {"userReaction": 0}})

        cursor = self.delegate.collection.aggregate(pipeline)
        items = [ProductPublic.model_validate(doc) for doc in cursor]

        total = self.delegate.collection.count_documents(criteria)

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
        pipeline = [
            {"$match": {"_id": ObjectId(str(product_id))}},
            {
                "$lookup": {
                    "from": "channels",
                    "localField": "channel_id",
                    "foreignField": "_id",
                    "as": "channel",
                }
            },
            {
                "$addFields": {
                    "channel": {
                        "$arrayElemAt": ["$channel", 0]
                    }
                }
            },
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
                                        {
                                            "$eq": [
                                                "$target_type",
                                                ReactionTarget.PRODUCT.value,
                                            ]
                                        },
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
        ]

        docs = list(self.delegate.collection.aggregate(pipeline))
        if not docs:
            return None
        return ProductPublic.model_validate(docs[0])

    def find_all(
        self, sort_by: str = None, sort_desc: bool = True, pagination: Pagination = None
    ) -> PaginatedResponse[ProductPublic]:
        pipeline = []
        
        if sort_by:
            order = DESCENDING if sort_desc else ASCENDING
            pipeline.append({"$sort": {sort_by: order}})

        if pagination:
            page, size = (pagination.page, pagination.size) if pagination else (1, 0)
            skip = (page - 1) * size
            pipeline.append({"$skip": skip})
            pipeline.append({"$limit": size})

        pipeline.append(
            {
                "$lookup": {
                    "from": "channels",
                    "localField": "channel_id",
                    "foreignField": "_id",
                    "as": "channel",
                }
            }
        )
        
        pipeline.append(
            {
                "$addFields": {
                    "channel": {
                        "$arrayElemAt": ["$channel", 0]
                    }
                }
            }
        )
        
        cursor = self.delegate.collection.aggregate(pipeline)
        items = [ProductPublic.model_validate(doc) for doc in cursor]
        
        total = self.delegate.collection.count_documents({})
        
        page, size = (pagination.page, pagination.size) if pagination else (1, 0)
        
        return PaginatedResponse(
            page=page,
            page_size=size,
            total=total,
            items=items,
        )

    def find_one(self, id: PyObjectId) -> ProductPublic | None:
        pipeline = [
            {"$match": {"_id": ObjectId(str(id))}},
            {
                "$lookup": {
                    "from": "channels",
                    "localField": "channel_id",
                    "foreignField": "_id",
                    "as": "channel",
                }
            },
            {
                "$addFields": {
                    "channel": {
                        "$arrayElemAt": ["$channel", 0]
                    }
                }
            },
        ]
        
        docs = list(self.delegate.collection.aggregate(pipeline))
        if not docs:
            return None
        return ProductPublic.model_validate(docs[0])

    def find_bookmarked_with_query(
        self,
        user_id: PyObjectId,
        query: str | None = None,
        pagination: Pagination | None = None,
        sort_by: str | None = None,
        sort_desc: bool = True,
    ) -> PaginatedResponse[ProductPublic]:
        criteria: dict = {}
        if query:
            criteria["$or"] = [
                {"name": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
            ]

        page, size = (pagination.page, pagination.size) if pagination else (1, 0)
        skip = (page - 1) * size
        order = DESCENDING if sort_desc else ASCENDING

        base_pipeline: list[dict] = [
            {"$match": criteria},
            {
                "$lookup": {
                    "from": "bookmarks",
                    "let": {"pid": "$_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$product_id", "$$pid"]},
                                        {"$eq": ["$user_id", ObjectId(str(user_id))]},
                                    ]
                                }
                            }
                        },
                        {"$project": {"_id": 1}},
                    ],
                    "as": "userBookmark",
                }
            },
            {"$match": {"userBookmark.0": {"$exists": True}}},
            {
                "$lookup": {
                    "from": "channels",
                    "localField": "channel_id",
                    "foreignField": "_id",
                    "as": "channel",
                }
            },
            {
                "$addFields": {
                    "channel": {
                        "$arrayElemAt": ["$channel", 0]
                    }
                }
            },
            {"$project": {"userBookmark": 0}},
        ]

        count_pipeline = base_pipeline + [{"$count": "count"}]
        count_res = list(self.delegate.collection.aggregate(count_pipeline))
        total = count_res[0]["count"] if count_res else 0

        page_pipeline = base_pipeline.copy()
        if sort_by:
            page_pipeline.append({"$sort": {sort_by: order}})
        if pagination:
            page_pipeline += [{"$skip": skip}, {"$limit": size}]

        cursor = self.delegate.collection.aggregate(page_pipeline)
        items = [ProductPublic.model_validate(doc) for doc in cursor]

        return PaginatedResponse(
            page=page,
            page_size=size,
            total=total,
            items=items,
        )

    def find_all_by(
        self,
        sort_by: str = None,
        sort_desc: bool = True,
        pagination: Pagination = None,
        **kwargs,
    ) -> PaginatedResponse[ProductPublic]:
        pipeline = [{"$match": kwargs}]
        
        if sort_by:
            order = DESCENDING if sort_desc else ASCENDING
            pipeline.append({"$sort": {sort_by: order}})

        if pagination:
            page, size = (pagination.page, pagination.size) if pagination else (1, 0)
            skip = (page - 1) * size
            pipeline.append({"$skip": skip})
            pipeline.append({"$limit": size})

        pipeline.append(
            {
                "$lookup": {
                    "from": "channels",
                    "localField": "channel_id",
                    "foreignField": "_id",
                    "as": "channel",
                }
            }
        )
        
        pipeline.append(
            {
                "$addFields": {
                    "channel": {
                        "$arrayElemAt": ["$channel", 0]
                    }
                }
            }
        )
        
        cursor = self.delegate.collection.aggregate(pipeline)
        items = [ProductPublic.model_validate(doc) for doc in cursor]
        
        total = self.delegate.collection.count_documents(kwargs)
        
        page, size = (pagination.page, pagination.size) if pagination else (1, 0)
        
        return PaginatedResponse(
            page=page,
            page_size=size,
            total=total,
            items=items,
        )

    def find_one_by_dict(self, criteria: dict) -> ProductPublic | None:
        pipeline = [
            {"$match": criteria},
            {
                "$lookup": {
                    "from": "channels",
                    "localField": "channel_id",
                    "foreignField": "_id",
                    "as": "channel",
                }
            },
            {
                "$addFields": {
                    "channel": {
                        "$arrayElemAt": ["$channel", 0]
                    }
                }
            },
        ]
        
        docs = list(self.delegate.collection.aggregate(pipeline))
        if not docs:
            return None
        return ProductPublic.model_validate(docs[0])

    def delete_one(self, id: PyObjectId):
        return self.delegate.delete_one(id)

    def find_all_by_dict(
        self,
        criteria: dict,
        pagination: Pagination | None = None,
        sort_by: str | None = None,
        sort_desc: bool = True,
    ) -> PaginatedResponse[ProductPublic]:
        pipeline = [{"$match": criteria}]
        
        if sort_by:
            order = DESCENDING if sort_desc else ASCENDING
            pipeline.append({"$sort": {sort_by: order}})

        if pagination:
            page, size = (pagination.page, pagination.size) if pagination else (1, 0)
            skip = (page - 1) * size
            pipeline.append({"$skip": skip})
            pipeline.append({"$limit": size})

        pipeline.append(
            {
                "$lookup": {
                    "from": "channels",
                    "localField": "channel_id",
                    "foreignField": "_id",
                    "as": "channel",
                }
            }
        )
        
        pipeline.append(
            {
                "$addFields": {
                    "channel": {
                        "$arrayElemAt": ["$channel", 0]
                    }
                }
            }
        )
        
        cursor = self.delegate.collection.aggregate(pipeline)
        items = [ProductPublic.model_validate(doc) for doc in cursor]
        
        total = self.delegate.collection.count_documents(criteria)
        
        page, size = (pagination.page, pagination.size) if pagination else (1, 0)
        
        return PaginatedResponse(
            page=page,
            page_size=size,
            total=total,
            items=items,
        )

    def count_all_by_dict(self, criteria):
        return self.delegate.count_all_by_dict(criteria)

    def delete_all(self):
        return self.delegate.delete_all()
