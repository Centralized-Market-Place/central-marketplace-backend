from typing import List, Dict, Any
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from centeral_marketplace.reactions.core import ReactionTarget
from core import PyObjectId


class ProductPipelineBuilder:
    
    def __init__(self):
        self.pipeline: List[Dict[str, Any]] = []
    
    def match_criteria(self, criteria: dict) -> 'ProductPipelineBuilder':
        self.pipeline.append({"$match": criteria})
        return self
    
    def lookup_channel(self) -> 'ProductPipelineBuilder':
        self.pipeline.extend([
            {
                "$lookup": {
                    "from": "channels",
                    "localField": "channel_id",
                    "foreignField": "_id",
                    "as": "channel",
                }
            },
            {"$addFields": {"channel": {"$arrayElemAt": ["$channel", 0]}}},
            {
                "$match": {
                    "$or": [
                        {"channel.is_suspended": {"$exists": False}},
                        {"channel.is_suspended": {"$ne": True}}
                    ]
                }
            }
        ])
        return self
    
    def unwind_channel(self) -> 'ProductPipelineBuilder':
        if (self.pipeline and 
            self.pipeline[-1].get("$addFields", {}).get("channel")):
            self.pipeline.pop()
        
        self.pipeline.append({"$unwind": "$channel"})
        return self
    
    def lookup_user_reactions(self, user_id: PyObjectId) -> 'ProductPipelineBuilder':
        self.pipeline.append({
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
        })
        
        self.pipeline.extend([
            {
                "$addFields": {
                    "user_reaction": {
                        "$arrayElemAt": ["$userReaction.reaction_type", 0]
                    }
                }
            },
            {"$project": {"userReaction": 0}},
        ])
        return self
    
    def lookup_bookmarks(self, user_id: PyObjectId) -> 'ProductPipelineBuilder':
        self.pipeline.extend([
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
                    ],
                    "as": "userBookmark",
                }
            },
            {"$match": {"userBookmark.0": {"$exists": True}}},
            {"$project": {"userBookmark": 0}},
        ])
        return self
    
    def add_semantic_search(self, query_vector: List[float], k: int = 100) -> 'ProductPipelineBuilder':
        search_stage = {
            "$search": {
                "index": "default", 
                "knnBeta": {
                    "vector": query_vector,
                    "path": "embedding",
                    "k": k
                }
            }
        }
        self.pipeline.insert(0, search_stage)
        return self
    
    def add_search_score(self) -> 'ProductPipelineBuilder':
        self.pipeline.append({
            "$addFields": {
                "search_score": {"$meta": "searchScore"}
            }
        })
        return self
    
    def sort_by(self, field: str, desc: bool = True) -> 'ProductPipelineBuilder':
        order = DESCENDING if desc else ASCENDING
        self.pipeline.append({"$sort": {field: order}})
        return self
    
    def create_facet_with_pagination(self, page: int, size: int) -> 'ProductPipelineBuilder':
        skip = (page - 1) * size if page > 0 else 0
        
        facet_stage = {
            "$facet": {
                "items": [
                    {"$skip": skip},
                    {"$limit": size}
                ] if size > 0 else [],
                "total": [{"$count": "count"}]
            }
        }
        self.pipeline.append(facet_stage)
        return self
    
    def build(self) -> List[Dict[str, Any]]:
        return self.pipeline
    
    @classmethod
    def base_product_criteria(cls) -> dict:
        return {"is_deleted": {"$ne": True}}
    
    @classmethod
    def create_text_search_criteria(cls, query: str, base_criteria: dict = None) -> dict:
        criteria = base_criteria.copy() if base_criteria else cls.base_product_criteria()
        if query:
            criteria["$text"] = {"$search": query}
        return criteria 