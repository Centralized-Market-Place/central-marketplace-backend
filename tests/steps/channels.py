from datetime import datetime
from centeral_marketplace.channels.core import Channel
from centeral_marketplace.channels.repository import ChannelRepository
from core import PyObjectId


def there_is_a_channel(
    channel_id: PyObjectId = None,
    telegram_id: int = 123456789,
    title: str = "Test Channel",
    username: str = "test_channel",
    description: str = "A test channel",
    total_products: int = 0,
    participants: int = 100,
    trust_score: int = 85,
    verified: bool = True,
    broadcast: bool = True,
):
    def step(context):
        channel_repo: ChannelRepository = context.injector.get(ChannelRepository)

        channel = Channel(
            id=channel_id,
            telegram_id=telegram_id,
            title=title,
            username=username,
            description=description,
            total_products=total_products,
            participants=participants,
            trust_score=trust_score,
            verified=verified,
            broadcast=broadcast,
            date_created=datetime.now(),
        )

        saved_channel = channel_repo.save(channel)
        context.channel = saved_channel
        return saved_channel

    return step


def there_are_multiple_channels(channels_data: list[dict]):
    def step(context):
        channel_repo: ChannelRepository = context.injector.get(ChannelRepository)

        channels = []
        for data in channels_data:
            channel = Channel(
                telegram_id=data.get("telegram_id", 123456789),
                title=data.get("title", "Test Channel"),
                username=data.get("username", "test_channel"),
                description=data.get("description", "A test channel"),
                total_products=data.get("total_products", 0),
                participants=data.get("participants", 100),
                trust_score=data.get("trust_score", 85),
                verified=data.get("verified", True),
                broadcast=data.get("broadcast", True),
                date_created=datetime.now(),
            )
            saved_channel = channel_repo.save(channel)
            channels.append(saved_channel)

        context.channels = channels
        return channels

    return step
