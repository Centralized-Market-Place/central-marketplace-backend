from centeral_marketplace.sellers.core import (
    SellerApplication,
    SellerApplicationStatus,
    SellerInfo,
)
from centeral_marketplace.sellers.repository import SellerApplicationRepository
from core import PyObjectId


def there_is_a_seller_application(
    user_id: PyObjectId,
    business_name: str = "Test Business",
    tin_number: str = "1234567890",
    channel_id: str = "@test_channel",
    channel_name: str = "Test Channel",
    government_id: str = "https://example.com/id.jpg",
    status: SellerApplicationStatus = SellerApplicationStatus.PENDING,
    admin_review_notes: str = None,
    has_bot_admin_access: bool = True,
    verified_channel_ownership: bool = True,
):
    def step(context):
        seller_repo: SellerApplicationRepository = context.injector.get(
            SellerApplicationRepository
        )

        seller_info = SellerInfo(
            business_name=business_name,
            tin_number=tin_number,
            channel_id=channel_id,
            channel_name=channel_name,
            government_id=government_id,
            has_bot_admin_access=has_bot_admin_access,
            verified_channel_ownership=verified_channel_ownership,
        )

        application = SellerApplication(
            user_id=user_id,
            seller_info=seller_info,
            status=status,
            admin_review_notes=admin_review_notes,
        )

        saved_application = seller_repo.save(application)
        context.seller_application = saved_application

    return step


def there_are_multiple_seller_applications(applications_data: list[dict]):
    def step(context):
        seller_repo: SellerApplicationRepository = context.injector.get(
            SellerApplicationRepository
        )
        applications = []

        for app_data in applications_data:
            user_id = app_data["user_id"]
            seller_info = SellerInfo(
                business_name=app_data.get("business_name", "Test Business"),
                tin_number=app_data.get("tin_number", "1234567890"),
                channel_id=app_data.get("channel_id", "@test_channel"),
                channel_name=app_data.get("channel_name", "Test Channel"),
                government_id=app_data.get(
                    "government_id", "https://example.com/id.jpg"
                ),
                has_bot_admin_access=app_data.get("has_bot_admin_access", True),
                verified_channel_ownership=app_data.get(
                    "verified_channel_ownership", True
                ),
            )

            application = SellerApplication(
                user_id=user_id,
                seller_info=seller_info,
                status=app_data.get("status", SellerApplicationStatus.PENDING),
                admin_review_notes=app_data.get("admin_review_notes"),
            )

            saved_application = seller_repo.save(application)
            applications.append(saved_application)

        context.seller_applications = applications

    return step
