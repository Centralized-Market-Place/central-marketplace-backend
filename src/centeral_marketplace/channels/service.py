from dataclasses import dataclass
import logging
from centeral_marketplace.infrastructure.json import Pagination, PaginatedResponse
from centeral_marketplace.channels.core import Channel, UpdateChannel
from centeral_marketplace.channels.repository import ChannelRepository
from centeral_marketplace.sellers.service import SellerService
from centeral_marketplace.users.repository import UserRepository
from fastapi import HTTPException, status
from injector import inject, singleton
from core import PyObjectId


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

@singleton
@inject
@dataclass
class ChannelService:
    channel_repository: ChannelRepository
    user_repository: UserRepository
    seller_service: SellerService

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
        try:
            channel = self.channel_repository.find_one(channel_id)
            return channel
        except Exception:
            logger.error(f"channel with id: {channel_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"channel with id: {channel_id} not found"
            )

    def get_my_channels(self, user_id: PyObjectId) -> list[Channel]:
        seller_applications = self.seller_service.get_approved_seller_applications(user_id)
        channel_ids = [seller_info.seller_info.channel_id for seller_info in seller_applications]
        channels = []
        for channel_id in channel_ids:
            channel = self.channel_repository.find_one_by_dict(
                {"$or": [{"username": channel_id}, {"telegram_id": channel_id}]}
            )
            if channel:
                channels.append(channel)

        return channels

    def save(self, channel: Channel) -> Channel:
        try:
            return self.channel_repository.save(channel)
        except Exception:
            logger.error(f"error saving channel: {channel}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"error saving channel: {channel}"
            )
    
    def update_channel(self, channel_id: PyObjectId, update_data: UpdateChannel) -> Channel:
        channel = self.channel_repository.find_one(channel_id)
        if not channel:
            logger.error(f"channel with id: {channel_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"channel with id: {channel_id} not found"
            )
        
        for key, value in update_data.model_dump(exclude_unset=True).items():
            setattr(channel, key, value)
        
        return self.channel_repository.save(channel)
        
