from datetime import datetime
from centeral_marketplace.products.core import Product
from centeral_marketplace.products.repository import ProductRepository
from core import PyObjectId


def there_is_a_product(
    product_id: PyObjectId = None,
    channel_id: PyObjectId = None,
    telegram_channel_id: int = 123456789,
    message_id: int = 1,
    title: str = "Test Product",
    description: str = "A test product",
    price: float = 100.0,
    views: int = 50,
    forwards: int = 5,
    is_available: bool = True,
    upvotes: int = 10,
    downvotes: int = 2,
    shares: int = 3,
    comments: int = 1,
    clicks: int = 25,
    categories: list = None,
):
    def step(context):
        product_repo: ProductRepository = context.injector.get(ProductRepository)

        product = Product(
            id=product_id,
            channel_id=channel_id,
            date=datetime.now(),
            telegram_channel_id=telegram_channel_id,
            message_id=message_id,
            title=title,
            description=description,
            price=price,
            views=views,
            forwards=forwards,
            is_available=is_available,
            upvotes=upvotes,
            downvotes=downvotes,
            shares=shares,
            comments=comments,
            clicks=clicks,
            categories=categories or [],
        )

        saved_product = product_repo.save(product)
        context.product = saved_product
        return saved_product

    return step


def there_are_multiple_products(products_data: list[dict]):
    def step(context):
        product_repo: ProductRepository = context.injector.get(ProductRepository)

        products = []
        for data in products_data:
            product = Product(
                channel_id=data.get("channel_id"),
                date=datetime.now(),
                telegram_channel_id=data.get("telegram_channel_id", 123456789),
                message_id=data.get("message_id", 1),
                title=data.get("title", "Test Product"),
                description=data.get("description", "A test product"),
                price=data.get("price", 100.0),
                views=data.get("views", 50),
                forwards=data.get("forwards", 5),
                is_available=data.get("is_available", True),
                upvotes=data.get("upvotes", 10),
                downvotes=data.get("downvotes", 2),
                shares=data.get("shares", 3),
                comments=data.get("comments", 1),
                clicks=data.get("clicks", 25),
                categories=data.get("categories", []),
            )
            saved_product = product_repo.save(product)
            products.append(saved_product)

        context.products = products
        return products

    return step
