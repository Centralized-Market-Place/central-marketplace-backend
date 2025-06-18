from dataclasses import dataclass
from datetime import UTC, datetime
import logging
import traceback

from centeral_marketplace.channels.repository import ChannelRepository
from fastapi import HTTPException, status
from injector import inject, singleton
from pymongo.errors import DuplicateKeyError

from centeral_marketplace.infrastructure.json import Pagination, PaginatedResponse
from centeral_marketplace.infrastructure.telegram.service import TelegramService
from centeral_marketplace.products.repository import ProductRepository
from centeral_marketplace.sellers.core import (
    SellerAnalytics,
    SellerApplication,
    SellerApplicationCreate,
    SellerApplicationReview,
    SellerApplicationStatus,
    SellerApplicationUpdate,
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
    channel_repo: ChannelRepository
    product_repository: ProductRepository
    config: Config

    def verify_bot_admin_status(
        self, user: User, channel_id: str
    ) -> TelegramBotStatusResponse:
        try:
            if not user.telegram:
                logger.error(
                    f"User {user.id} attempted bot admin verification without Telegram login"
                )
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
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error verifying bot admin status for user {user.id} and channel {channel_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to verify bot admin status",
            ) from e

    def is_verified_channel_admin(self, user: User, channel_id: str) -> bool:
        try:
            if not user.telegram:
                return False

            bot_status = self.verify_bot_admin_status(user, channel_id)
            return (
                bot_status.has_bot_admin_access
                and bot_status.verified_channel_ownership
            )
        except Exception:
            logger.error(
                f"Error checking channel admin status for user {user.id}: {traceback.format_exc()}"
            )
            return False

    def save_seller_application(
        self, user: User, application_data: SellerApplicationCreate
    ) -> SellerApplication:
        try:
            if not user.telegram:
                logger.error(
                    f"User {user.id} attempted seller application without Telegram login"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is not logged in with Telegram",
                )

            existing_applications = self.seller_repository.find_by_user_id(user.id)

            for app in existing_applications:
                if app.status == SellerApplicationStatus.PENDING:
                    logger.error(
                        f"User {user.id} already has pending seller application"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="User already has a pending seller application",
                    )

            bot_status = self.verify_bot_admin_status(user, application_data.channel_id)

            if not bot_status.has_bot_admin_access:
                logger.error(
                    f"Bot not admin in channel {application_data.channel_id} for user {user.id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bot is not added as an admin to the channel",
                )

            if not bot_status.verified_channel_ownership:
                logger.error(
                    f"User {user.id} not owner of channel {application_data.channel_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is not the owner of the channel",
                )
            
            channel_id = application_data.channel_id

            if channel_id.startswith("@"):
                channel_id = channel_id[1:]
                
            seller_info = SellerInfo(
                business_name=application_data.business_name,
                tin_number=application_data.tin_number,
                channel_id=channel_id,
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

            saved_application = self.seller_repository.save(application)
            logger.info(f"Seller application created for user {user.id}")
            return saved_application
        except HTTPException:
            raise
        except DuplicateKeyError:
            logger.error(
                f"Duplicate seller application for channel {application_data.channel_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An application for this channel already exists",
            )
        except Exception as e:
            logger.error(
                f"Error saving seller application for user {user.id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to save seller application",
            ) from e

    def get_approved_seller_applications(
        self, user_id: PyObjectId
    ) -> list[SellerApplication]:
        try:
            applications = self.seller_repository.find_all_by_dict(
                criteria={
                    "user_id": user_id,
                    "status": SellerApplicationStatus.APPROVED,
                },
                sort_by="created_at",
                sort_desc=True,
            ).items
            return applications
        except Exception as e:
            logger.error(
                f"Error getting approved seller applications for user {user_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to get approved seller applications",
            ) from e

    def get_all_seller_applications(
        self,
        pagination: Pagination = None,
        application_status: SellerApplicationStatus = None,
        search: str = None,
    ) -> PaginatedResponse[SellerApplication]:
        try:
            criteria = {}
            if application_status:
                criteria["status"] = application_status
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
        except Exception as e:
            logger.error(f"Error getting seller applications: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve seller applications",
            ) from e

    def get_user_seller_applications(
        self, user_id: PyObjectId
    ) -> list[SellerApplication]:
        try:
            return self.seller_repository.find_by_user_id(user_id)
        except Exception as e:
            logger.error(
                f"Error getting seller applications for user {user_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve user seller applications",
            ) from e

    def get_seller_application(self, application_id: PyObjectId) -> SellerApplication:
        try:
            return self.seller_repository.find_one(application_id)
        except Exception as e:
            logger.error(
                f"Error getting seller application {application_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Seller application with ID {application_id} not found",
            ) from e

    def update_seller_application(
        self,
        user: User,
        application_id: PyObjectId,
        application_data: SellerApplicationUpdate,
    ) -> SellerApplication:
        try:
            application = self.get_seller_application(application_id)
            if str(application.user_id) != str(user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not allowed to update this application",
                )
            if application.status != SellerApplicationStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only pending applications can be updated",
                )

            for key, value in application_data.model_dump(exclude_unset=True).items():
                setattr(application.seller_info, key, value)

            updated_application = self.seller_repository.save(application)
            logger.info(f"Seller application updated for user {user.id}")
            return updated_application
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error updating seller application {application_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to update seller application",
            ) from e

    def delete_seller_application(self, user: User, application_id: PyObjectId) -> None:
        try:
            application = self.get_seller_application(application_id)
            if str(application.user_id) != str(user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not allowed to delete this application",
                )
            if application.status == SellerApplicationStatus.APPROVED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete approved applications",
                )

            self.seller_repository.delete_one(application_id)
            logger.info(f"Seller application deleted for user {user.id}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error deleting seller application {application_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to delete seller application",
            ) from e

    def review_seller_application(
        self, review: SellerApplicationReview
    ) -> SellerApplication:
        try:
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
                    self.channel_repo.save(channel)
                user = self.user_repository.find_one(application.user_id)
                if user:
                    user.role = Role.SELLER
                    user.updated_at = datetime.now(UTC)
                    self.user_repository.save(user)
                    logger.info(
                        f"Approved seller application {application.id} for user {user.id}"
                    )

            return updated_application
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error reviewing seller application {review.application_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to review seller application",
            ) from e

    def get_seller_analytics(self, user_id: PyObjectId) -> SellerAnalytics:
        try:
            approved_applications = self.get_approved_seller_applications(user_id)

            if not approved_applications:
                logger.error(f"User {user_id} has no approved seller applications")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User has no approved seller applications",
                )

            total_channels = len(approved_applications)
            total_products = 0
            total_views = 0
            total_prices = []
            total_available_products = 0

            for application in approved_applications:
                channel_id = application.seller_info.channel_id

                channel = self.channel_repo.find_one_by_dict(
                    {"$or": [{"username": channel_id}, {"telegram_id": channel_id}]}
                )

                if channel:
                    channel_analytics_data = (
                        self.product_repository.get_channel_analytics(channel.id)
                    )

                    total_products += channel_analytics_data["total_products"]
                    total_views += channel_analytics_data["total_views"]
                    total_available_products += channel_analytics_data[
                        "available_products"
                    ]

                    if channel_analytics_data["total_products"] > 0:
                        total_prices.append(
                            channel_analytics_data["average_price"]
                            * channel_analytics_data["total_products"]
                        )

            average_price = (
                sum(total_prices) / total_products if total_products > 0 else 0.0
            )
            availability_percentage = (
                (total_available_products / total_products * 100)
                if total_products > 0
                else 0.0
            )

            return SellerAnalytics(
                total_channels=total_channels,
                total_products=total_products,
                total_views=total_views,
                average_price=average_price,
                availability_percentage=availability_percentage,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error getting seller analytics for user {user_id}: {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to retrieve seller analytics",
            ) from e
