from dataclasses import dataclass
from datetime import UTC, datetime
import logging
from centeral_marketplace.channels.service import ChannelService
from fastapi import HTTPException, status
from injector import inject, singleton
from pymongo.errors import DuplicateKeyError

from centeral_marketplace.infrastructure.json import Pagination, PaginatedResponse
from centeral_marketplace.infrastructure.telegram.service import TelegramService
from centeral_marketplace.sellers.core import (
    SellerApplication,
    SellerApplicationCreate,
    SellerApplicationReview,
    SellerApplicationStatus,
    SellerInfo,
    TelegramBotStatusResponse,
)
from centeral_marketplace.sellers.repository import SellerApplicationRepository
from centeral_marketplace.users.core import Role, User
from centeral_marketplace.users.repository import UserRepository
from config import Config
from core import PyObjectId

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


@singleton
@inject
@dataclass
class SellerService:
    seller_repository: SellerApplicationRepository
    user_repository: UserRepository
    telegram_service: TelegramService
    channel_service: ChannelService
    config: Config

    def verify_bot_admin_status(
        self, user: User, channel_id: str
    ) -> TelegramBotStatusResponse:
        if not user.telegram:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not logged in with Telegram",
            )

        has_bot_admin_access = self.telegram_service.is_bot_admin(channel_id)
        verified_channel_ownership = self.telegram_service.verify_channel_ownership(
            user.telegram.telegram_id, channel_id
        )

        return TelegramBotStatusResponse(
            has_bot_admin_access=has_bot_admin_access,
            verified_channel_ownership=verified_channel_ownership,
        )

    def is_verified_channel_admin(self, user: User, channel_id: str) -> bool:
        if not user.telegram:
            return False

        bot_status = self.verify_bot_admin_status(user, channel_id)
        return bot_status.has_bot_admin_access and bot_status.verified_channel_ownership

    def save_seller_application(
        self, user: User, application_data: SellerApplicationCreate
    ) -> SellerApplication:
        if not user.telegram:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not logged in with Telegram",
            )

        existing_applications = self.seller_repository.find_by_user_id(user.id)

        for app in existing_applications:
            if app.status == SellerApplicationStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User already has a pending seller application",
                )

        bot_status = self.verify_bot_admin_status(user, application_data.channel_id)

        if not bot_status.has_bot_admin_access:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bot is not added as an admin to the channel",
            )

        if not bot_status.verified_channel_ownership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not the owner of the channel",
            )

        seller_info = SellerInfo(
            business_name=application_data.business_name,
            tin_number=application_data.tin_number,
            channel_id=application_data.channel_id,
            channel_name=application_data.channel_name,
            government_id=application_data.government_id,
            has_bot_admin_access=bot_status.has_bot_admin_access,
            verified_channel_ownership=bot_status.verified_channel_ownership,
        )

        now = datetime.now(UTC)
        application = SellerApplication(
            user_id=user.id,
            seller_info=seller_info,
            status=SellerApplicationStatus.PENDING,
            created_at=now,
        )

        try:
            return self.seller_repository.save(application)
        except DuplicateKeyError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An application for this channel already exists",
            )

    def get_all_seller_applications(
        self,
        pagination: Pagination = None,
        status: SellerApplicationStatus = None,
        search: str = None,
    ) -> PaginatedResponse[SellerApplication]:
        criteria = {}
        if status:
            criteria["status"] = status
        if search:
            criteria["$or"] = [
                {"seller_info.business_name": {"$regex": search, "$options": "i"}},
                {"seller_info.channel_name": {"$regex": search, "$options": "i"}},
            ]
        return self.seller_repository.find_all_by_dict(
            criteria=criteria,
            pagination=pagination,
            sort_by="created_at",
            sort_desc=True,
        )

    def get_user_seller_applications(
        self, user_id: PyObjectId
    ) -> list[SellerApplication]:
        return self.seller_repository.find_by_user_id(user_id)

    def get_seller_application(self, application_id: PyObjectId) -> SellerApplication:
        application = self.seller_repository.find_one(application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seller application not found",
            )
        return application

    def review_seller_application(
        self, review: SellerApplicationReview
    ) -> SellerApplication:

        application = self.get_seller_application(review.application_id)

        application.status = review.status
        application.admin_review_notes = review.admin_review_notes
        application.updated_at = datetime.now(UTC)

        updated_application = self.seller_repository.save(application)

        if review.status == SellerApplicationStatus.APPROVED:
            channel = self.telegram_service.get_channel_info(
                application.seller_info.channel_id
            )
            if channel:
                channel.verified = True
                self.channel_service.save(channel)
            user = self.user_repository.find_one(application.user_id)
            if user:
                user.role = Role.SELLER
                user.seller_infos.append(application.seller_info)
                user.updated_at = datetime.now(UTC)
                self.user_repository.save(user)

        return updated_application
