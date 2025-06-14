from typing import Annotated, Optional
from core import PyObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_injector import Injected

from centeral_marketplace.infrastructure.json import (
    Pagination,
    PaginatedResponse,
)
from centeral_marketplace.sellers.core import (
    SellerAnalytics,
    SellerApplication,
    SellerApplicationCreate,
    SellerApplicationReview,
    SellerApplicationStatus,
    SellerApplicationUpdate,
    TelegramBotStatusResponse,
)
from centeral_marketplace.sellers.service import SellerService
from centeral_marketplace.users.core import Role, User
from middleware import get_current_user, require_role


sellers_router = APIRouter(
    prefix="/sellers",
    tags=["sellers"],
)


@sellers_router.get(
    "/bot-status/{channel_id}", response_model=TelegramBotStatusResponse
)
async def check_bot_status(
    channel_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    seller_service: SellerService = Injected(SellerService),
):
    return seller_service.verify_bot_admin_status(current_user, channel_id)


@sellers_router.post(
    "/apply", response_model=SellerApplication, status_code=status.HTTP_201_CREATED
)
async def apply_seller(
    application: SellerApplicationCreate,
    current_user: Annotated[User, Depends(require_role([Role.USER, Role.SELLER]))],
    seller_service: SellerService = Injected(SellerService),
):
    return seller_service.save_seller_application(current_user, application)


@sellers_router.get(
    "/applications", response_model=PaginatedResponse[SellerApplication]
)
async def get_all_seller_applications(
    _: Annotated[User, Depends(require_role([Role.ADMIN, Role.SUPER_ADMIN]))],
    page: int = 1,
    page_size: int = 10,
    application_status: Optional[SellerApplicationStatus] = Query(
        None, description="Filter by application status"
    ),
    search: Optional[str] = Query(
        None, description="Search by channel name or business name"
    ),
    seller_service: SellerService = Injected(SellerService),
):
    pagination = Pagination(page=page, size=page_size)
    return seller_service.get_all_seller_applications(
        pagination=pagination, application_status=application_status, search=search
    )


@sellers_router.get("/applications/me", response_model=list[SellerApplication])
async def get_my_seller_applications(
    current_user: Annotated[User, Depends(get_current_user)],
    seller_service: SellerService = Injected(SellerService),
):
    return seller_service.get_user_seller_applications(current_user.id)


@sellers_router.get("/applications/{application_id}", response_model=SellerApplication)
async def get_seller_application(
    application_id: PyObjectId,
    current_user: Annotated[User, Depends(get_current_user)],
    seller_service: SellerService = Injected(SellerService),
):
    application = seller_service.get_seller_application(application_id)

    if (
        current_user.role != Role.ADMIN
        and current_user.role != Role.SUPER_ADMIN
        and str(application.user_id) != str(current_user.id)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this application",
        )

    return application


@sellers_router.post("/applications/{application_id}", response_model=SellerApplication)
async def update_seller_application(
    application_id: PyObjectId,
    application: SellerApplicationUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    seller_service: SellerService = Injected(SellerService),
):
    return seller_service.update_seller_application(
        current_user, application_id, application
    )


@sellers_router.delete(
    "/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_seller_application(
    application_id: PyObjectId,
    current_user: Annotated[User, Depends(get_current_user)],
    seller_service: SellerService = Injected(SellerService),
):
    seller_service.delete_seller_application(current_user, application_id)


@sellers_router.post(
    "/applications/{application_id}/review", response_model=SellerApplication
)
async def review_seller_application(
    application_id: PyObjectId,
    review: SellerApplicationReview,
    _: Annotated[User, Depends(require_role([Role.ADMIN, Role.SUPER_ADMIN]))],
    seller_service: SellerService = Injected(SellerService),
):
    if application_id != review.application_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application ID in path must match the one in the request body",
        )

    return seller_service.review_seller_application(review)


@sellers_router.get("/analytics", response_model=SellerAnalytics)
async def get_seller_analytics(
    current_user: Annotated[User, Depends(require_role([Role.SELLER]))],
    seller_service: SellerService = Injected(SellerService),
):
    return seller_service.get_seller_analytics(current_user.id)
