from dataclasses import dataclass
from centeral_marketplace.infrastructure.json import Pagination, PaginatedResponse
from centeral_marketplace.channels.core import Channel
from centeral_marketplace.channels.repository import ChannelRepository
from injector import inject, singleton

from core import PyObjectId


@singleton
@inject
@dataclass
class ChannelService:
    channel_repository: ChannelRepository

    def find_all(
        self,
        pagination: Pagination = None,
        sort_by: str = None,
        sort_desc: bool = True,
        criteria: dict = None,
    ) -> PaginatedResponse[Channel]:
        if criteria is None:
            criteria = {}
        return self.channel_repository.find_all_by_dict(
            pagination=pagination,
            sort_by=sort_by,
            sort_desc=sort_desc,
            criteria=criteria,
        )

    def count_all_by_dict(self, criteria: dict) -> int:
        return self.channel_repository.count_all_by_dict(criteria)

    def find_one(self, channel_id: PyObjectId) -> Channel:
        return self.channel_repository.find_one(channel_id)
