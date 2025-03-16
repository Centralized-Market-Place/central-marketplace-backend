from centeral_marketplace.infrastructure.json import PaginatedResponse, Pagination, RestConverter
from centeral_marketplace.channels.service import ChannelService
from fastapi import APIRouter
from fastapi_injector import Injected

channel_router = APIRouter(
    prefix="/channels",
    tags=["channels"],
)

@channel_router.get("/", response_model=PaginatedResponse)
async def get_channels(
    page: int = 1,
    page_size: int = 20,
    sort_by: str = None,
    sort_desc: bool = True,
    query: str = None,
    channel_service: ChannelService = Injected(ChannelService),
    converter: RestConverter = Injected(RestConverter),
):
    criteria = {}

    if query:
        criteria["$or"] = [
            {"name": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}},
        ]

    total = channel_service.count_all_by_dict(criteria=criteria)
    channels = list(
        channel_service.find_all(
            pagination=Pagination(page=page, size=page_size),
            sort_by=sort_by,
            sort_desc=sort_desc,
            criteria=criteria,
        )
    )

    return PaginatedResponse(
        page=page,
        page_size=page_size,
        total=total,
        items=converter.unstructure(channels),
    )


@channel_router.get("/{channel_id}")
async def get_channel(
    channel_id: int,
    channel_service: ChannelService = Injected(ChannelService),
    converter: RestConverter = Injected(RestConverter),
):
    channel = channel_service.find_one(channel_id)
    return converter.unstructure(channel)
