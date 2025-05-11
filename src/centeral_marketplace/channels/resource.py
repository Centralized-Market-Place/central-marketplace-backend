from centeral_marketplace.channels.core import Channel
from centeral_marketplace.infrastructure.json import (
    PaginatedResponse,
    Pagination,
)
from centeral_marketplace.channels.service import ChannelService
from fastapi import APIRouter
from fastapi_injector import Injected

channel_router = APIRouter(
    prefix="/channels",
    tags=["channels"],
)


@channel_router.get("/", response_model=PaginatedResponse[Channel])
async def get_channels(
    page: int = 1,
    page_size: int = 20,
    sort_by: str = None,
    sort_desc: bool = True,
    query: str = None,
    channel_name: str = None,
    channel_service: ChannelService = Injected(ChannelService),
):
    criteria = {}

    if query:
        criteria["$or"] = [
            {"title": {"$regex": query, "$options": "i"}},
        ]

    paginated = channel_service.find_all(
        pagination=Pagination(page=page, size=page_size),
        sort_by=sort_by,
        sort_desc=sort_desc,
        criteria=criteria,
    )
    
    return paginated


@channel_router.get("/{channel_id}", response_model=Channel)
async def get_channel(
    channel_id: str,
    channel_service: ChannelService = Injected(ChannelService),
):
    channel = channel_service.find_one(channel_id)
    return channel
