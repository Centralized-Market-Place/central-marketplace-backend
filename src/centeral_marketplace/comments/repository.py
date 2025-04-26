from dataclasses import dataclass
from typing import Optional
from bson import ObjectId
from centeral_marketplace.reactions.core import ReactionTarget
from pymongo import DESCENDING, ASCENDING

from centeral_marketplace.infrastructure.json import PaginatedResponse, Pagination
from centeral_marketplace.infrastructure.mongo import MongoDBJsonRepositoryDelegate
from config import Config
from injector import inject, singleton
from centeral_marketplace.comments.core import Comment
from core import PyObjectId


@inject
@singleton
@dataclass
class CommentRepository:
    config: Config

    def __post_init__(self):
        self.delegate = MongoDBJsonRepositoryDelegate(
            collection_name="comments", model=Comment, config=self.config
        )

    def save(self, data: Comment):
        return self.delegate.save(data)

    def save_all(self, data: list[Comment]):
        return self.delegate.save_all(data)

    def find_one(self, id: PyObjectId) -> Optional[Comment]:
        return self.delegate.find_one(id)

    def find_all(
        self, sort_by: str = None, sort_desc: bool = True, pagination: Pagination = None
    ) -> PaginatedResponse[Comment]:
        return self.delegate.find_all(
            pagination=pagination, sort_by=sort_by, sort_desc=sort_desc
        )

    def find_all_by(
        self,
        sort_by: str = None,
        sort_desc: bool = True,
        pagination: Pagination = None,
        **kwargs,
    ) -> PaginatedResponse[Comment]:
        return self.delegate.find_all_by_dict(
            criteria=kwargs, pagination=pagination, sort_by=sort_by, sort_desc=sort_desc
        )

    def find_one_by_dict(self, criteria: dict) -> Comment:
        return self.delegate.find_one_by_dict(criteria)

    def delete_one(self, id: PyObjectId):
        return self.delegate.delete_one(id)

    def find_all_by_dict(
        self,
        criteria: dict,
        sort_by: str = None,
        sort_desc: bool = True,
        pagination: Pagination = None,
    ) -> PaginatedResponse[Comment]:
        return self.delegate.find_all_by_dict(
            criteria=criteria,
            pagination=pagination,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )

    def find_all_with_user_reaction(
        self,
        user_id: PyObjectId,
        criteria: dict,
        pagination: Pagination = None,
        sort_by: str = None,
        sort_desc: bool = True,
    ) -> PaginatedResponse[Comment]:
        page, size = (pagination.page, pagination.size) if pagination else (1, 0)
        skip = (page - 1) * size
        order = DESCENDING if sort_desc else ASCENDING

        pipeline: list[dict] = [
            {"$match": criteria},
        ]
        if sort_by:
            pipeline.append({"$sort": {sort_by: order}})
        if pagination:
            pipeline += [{"$skip": skip}, {"$limit": size}]

        pipeline += [
            {
                "$lookup": {
                    "from": "reactions",
                    "let": {"cid": "$_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$target_id", "$$cid"]},
                                        {"$eq": ["$user_id", ObjectId(str(user_id))]},
                                        {
                                            "$eq": [
                                                "$target_type",
                                                ReactionTarget.COMMENT.value,
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

        cursor = self.delegate.collection.aggregate(pipeline)
        items = [Comment.model_validate(doc) for doc in cursor]
        total = self.delegate.collection.count_documents(criteria)
        return PaginatedResponse(page=page, page_size=size, total=total, items=items)

    def find_one_with_user_reaction(
        self,
        comment_id: PyObjectId,
        user_id: PyObjectId,
    ) -> Comment | None:
        pipeline = [
            {"$match": {"_id": ObjectId(str(comment_id))}},
            {
                "$lookup": {
                    "from": "reactions",
                    "let": {"cid": "$_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$target_id", "$$cid"]},
                                        {"$eq": ["$user_id", ObjectId(str(user_id))]},
                                        {
                                            "$eq": [
                                                "$target_type",
                                                ReactionTarget.COMMENT.value,
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
        return Comment.model_validate(docs[0]) if docs else None

    def count_all_by_dict(self, criteria: dict) -> int:
        return self.delegate.count_all_by_dict(criteria)

    def delete_all(self):
        return self.delegate.delete_all()
