from dataclasses import dataclass
from centeral_marketplace.infrastructure.json import Pagination, PaginatedResponse
from centeral_marketplace.reports.core import Report
from injector import inject, singleton
from centeral_marketplace.infrastructure.mongo import MongoDBJsonRepositoryDelegate
from centeral_marketplace.infrastructure.repository import RepositoryInterface
from config import Config
from core import PyObjectId


@inject
@singleton
@dataclass
class ReportRepository(RepositoryInterface[Report]):
    config: Config

    def __post_init__(self):
        self.delegate = MongoDBJsonRepositoryDelegate(
            collection_name="reports", model=Report, config=self.config
        )
        self.delegate.ensure_index("reporter_id", name="reports_reporter_id")
        self.delegate.ensure_index("target_id", name="reports_target_id")
        self.delegate.ensure_index("target_type", name="reports_target_type")
        self.delegate.ensure_index("status", name="reports_status")
        self.delegate.ensure_index("report_type", name="reports_report_type")
        self.delegate.ensure_index("created_at", name="reports_created_at")
        self.delegate.ensure_index(
            ["target_id", "target_type", "reporter_id"], 
            unique=True, 
            name="reports_unique_user_target"
        )

    def save(self, data: Report):
        return self.delegate.save(data)

    def save_all(self, data: list[Report]):
        return self.delegate.save_all(data)

    def find_all(
        self, sort_by: str = None, sort_desc: bool = True, pagination: Pagination = None
    ) -> PaginatedResponse[Report]:
        return self.delegate.find_all(
            pagination=pagination, sort_by=sort_by, sort_desc=sort_desc
        )

    def find_one(self, id: PyObjectId):
        return self.delegate.find_one(id)

    def find_all_by_dict(
        self,
        criteria: dict,
        pagination=None,
        sort_by: str | None = None,
        sort_desc: bool = True,
    ) -> PaginatedResponse[Report]:
        return self.delegate.find_all_by_dict(
            criteria=criteria,
            pagination=pagination,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )

    def find_one_by_dict(self, criteria: dict) -> Report:
        return self.delegate.find_one_by_dict(criteria)

    def count_all_by_dict(self, criteria):
        return self.delegate.count_all_by_dict(criteria)

    def delete_one(self, id: PyObjectId):
        return self.delegate.delete_one(id)

    def delete_all(self):
        return self.delegate.delete_all()

    def find_existing_report(self, reporter_id: PyObjectId, target_id: PyObjectId, target_type: str) -> Report:
        """Find if user has already reported this target"""
        criteria = {
            "reporter_id": reporter_id,
            "target_id": target_id,
            "target_type": target_type
        }
        return self.find_one_by_dict(criteria) 