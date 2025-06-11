from typing import Annotated
from centeral_marketplace.channels.core import Channel, ChannelAnalytics, UpdateChannel
from centeral_marketplace.infrastructure.json import (
    PaginatedResponse,
    Pagination,
)
from centeral_marketplace.channels.service import ChannelService
from centeral_marketplace.products.service import ProductService
from centeral_marketplace.users.core import Role, User
from core import PyObjectId
from fastapi import APIRouter, Depends
from fastapi_injector import Injected
from middleware import get_current_user, require_role

channel_router = APIRouter(
    prefix="/channels",
    tags=["channels"],
)


@channel_router.get("", response_model=PaginatedResponse[Channel])
async def get_channels(
    page: int = 1,
    page_size: int = 20,
    sort_by: str = None,
    sort_desc: bool = True,
    query: str = None,
    channel_service: ChannelService = Injected(ChannelService),
):
    criteria = {}

    if query:
        criteria["$text"] = {"$search": query}

    paginated = channel_service.find_all(
        pagination=Pagination(page=page, size=page_size),
        sort_by=sort_by,
        sort_desc=sort_desc,
        criteria=criteria,
    )

    return paginated

@channel_router.get("/me", response_model=list[Channel])
def get_my_channels(
    current_user: Annotated[User, Depends(require_role([Role.SELLER.value]))],
    channel_service: ChannelService = Injected(ChannelService),
):
    return channel_service.get_my_channels(current_user.id)


@channel_router.get("/{channel_id}", response_model=Channel)
async def get_channel(
    channel_id: PyObjectId,
    channel_service: ChannelService = Injected(ChannelService),
):
    channel = channel_service.find_one(channel_id)
    return channel


@channel_router.post("/{channel_id}", response_model=Channel)
async def update_channel(
    channel_id: PyObjectId,
    update_data: UpdateChannel,
    current_user: Annotated[User, Depends(get_current_user)],
    channel_service: ChannelService = Injected(ChannelService),
):
    return channel_service.update_channel(current_user, channel_id, update_data)

@channel_router.get("/{channel_id}/analytics", response_model=ChannelAnalytics)
async def get_channel_analytics(
    channel_id: PyObjectId,
    product_service: ProductService = Injected(ProductService),
):
    return product_service.get_channel_analytics(channel_id)