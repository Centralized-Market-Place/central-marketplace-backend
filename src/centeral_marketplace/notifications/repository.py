from typing import List, Optional
from dataclasses import dataclass
from injector import inject, singleton
from pymongo import ASCENDING, DESCENDING

from centeral_marketplace.infrastructure.json import PaginatedResponse, Pagination
from centeral_marketplace.infrastructure.mongo import MongoDBJsonRepositoryDelegate
from centeral_marketplace.notifications.core import Notification
from centeral_marketplace.infrastructure.repository import RepositoryInterface
from config import Config
from core import PyObjectId

import logging

logger = logging.getLogger(__name__)

@inject
@singleton
@dataclass
class NotificationRepository(RepositoryInterface[Notification]):
    config: Config

    def __post_init__(self):
        self.delegate = MongoDBJsonRepositoryDelegate(
            collection_name="notifications", 
            model=Notification, 
            config=self.config
        )
        self.delegate.ensure_index("user_id")
        self.delegate.ensure_index("read")
        self.delegate.ensure_compound_index(
            [("user_id", ASCENDING), ("created_at", DESCENDING)]
        )
    
    def save(self, notification: Notification) -> Notification:
        return self.delegate.save(notification)
    
    def save_all(self, notifications: List[Notification]) -> None:
        return self.delegate.save_all(notifications)
    
    def find_one(self, id: PyObjectId) -> Notification:
        return self.delegate.find_one(id)
    
    def find_all(
        self,
        pagination: Optional[Pagination] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = True
    ) -> PaginatedResponse[Notification]:
        return self.delegate.find_all(
            pagination=pagination,
            sort_by=sort_by,
            sort_desc=sort_desc
        )
    
    def find_all_by_dict(
        self,
        criteria: dict,
        pagination: Optional[Pagination] = None,
        sort_by: Optional[str] = "created_at",
        sort_desc: bool = True
    ) -> PaginatedResponse[Notification]:
        return self.delegate.find_all_by_dict(
            criteria=criteria,
            pagination=pagination,
            sort_by=sort_by,
            sort_desc=sort_desc
        )
    
    
    def count_all_by_dict(self, criteria: dict) -> int:
        return self.delegate.count_all_by_dict(criteria)
    
    def delete_one(self, id: PyObjectId) -> None:
        self.delegate.delete_one(id)

    def delete_all(self) -> None:
        self.delegate.delete_all()
    
    def delete_by_dict(self, criteria: dict) -> int:
        return self.delegate.delete_by_dict(criteria) 