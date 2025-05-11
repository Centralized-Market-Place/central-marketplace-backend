from dataclasses import dataclass
from centeral_marketplace.infrastructure.json import Pagination, PaginatedResponse
from centeral_marketplace.channels.core import Channel
from centeral_marketplace.channels.repository import ChannelRepository
from centeral_marketplace.users.repository import UserRepository
from injector import inject, singleton

from core import PyObjectId


@singleton
@inject
@dataclass
class ChannelService:
    channel_repository: ChannelRepository
    user_repository: UserRepository

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


    def find_one(self, channel_id: PyObjectId) -> Channel:
        return self.channel_repository.find_one(channel_id)
    
    def get_my_channels(self, user_id: PyObjectId) -> list[Channel]:
        seller_infos = self.user_repository.find_one(user_id).seller_infos
        channel_ids = [seller_info.channel_id for seller_info in seller_infos]
        channels = []
        for channel_id in channel_ids:
            channel = self.channel_repository.find_one_by_dict({
                "$or": [
                    {"username": channel_id},
                    {"telegram_id": channel_id}
                ]
            })
            if channel:
                channels.append(channel)
        
        return channels
        

    
    def save(self, channel: Channel) -> Channel:
        return self.channel_repository.save(channel)

