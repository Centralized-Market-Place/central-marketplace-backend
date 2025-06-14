from dataclasses import dataclass
from centeral_marketplace.infrastructure.json import Pagination, PaginatedResponse
from injector import inject, singleton
from centeral_marketplace.infrastructure.mongo import MongoDBJsonRepositoryDelegate
from centeral_marketplace.infrastructure.repository import RepositoryInterface
from centeral_marketplace.admin_invites.core import AdminInvitation
from config import Config
from core import PyObjectId


@inject
@singleton
@dataclass
class AdminInvitationRepository(RepositoryInterface[AdminInvitation]):
    config: Config

    def __post_init__(self):
        self.delegate = MongoDBJsonRepositoryDelegate(
            collection_name="admin_invitations",
            model=AdminInvitation,
            config=self.config,
        )
        self.delegate.ensure_index("email", unique=True, name="admin_invitations_email")
        self.delegate.ensure_index("token", unique=True, name="admin_invitations_token")
        self.delegate.ensure_index("expires_at", name="admin_invitations_expires_at")
        self.delegate.ensure_index("status", name="admin_invitations_status")
        self.delegate.ensure_index("created_at", name="admin_invitations_created_at")

    def save(self, data: AdminInvitation) -> AdminInvitation:
        return self.delegate.save(data)

    def save_all(self, data: list[AdminInvitation]) -> list[AdminInvitation]:
        return self.delegate.save_all(data)

    def find_all(
        self, sort_by: str = None, sort_desc: bool = True, pagination: Pagination = None
    ) -> PaginatedResponse[AdminInvitation]:
        return self.delegate.find_all(
            pagination=pagination, sort_by=sort_by, sort_desc=sort_desc
        )

    def find_one(self, id: PyObjectId) -> AdminInvitation:
        return self.delegate.find_one(id)

    def find_one_by_dict(self, criteria: dict) -> AdminInvitation:
        return self.delegate.find_one_by_dict(criteria)

    def find_all_by_dict(
        self,
        criteria: dict,
        pagination: Pagination = None,
        sort_by: str | None = None,
        sort_desc: bool = True,
    ) -> PaginatedResponse[AdminInvitation]:
        return self.delegate.find_all_by_dict(
            criteria=criteria,
            pagination=pagination,
            sort_by=sort_by,
            sort_desc=sort_desc,
        )

    def delete_one(self, id: PyObjectId):
        return self.delegate.delete_one(id)
    
    def delete_all(self):
        return self.delegate.delete_all()

    def count_all_by_dict(self, criteria: dict) -> int:
        return self.delegate.count_all_by_dict(criteria)
