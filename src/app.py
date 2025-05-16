import logging
from centeral_marketplace.users.core import UserCreate
from centeral_marketplace.users.service import UserService
from config import Config
from fastapi import FastAPI
from fastapi_injector import attach_injector
from injector import Injector
from utils import create_injector
from fastapi.middleware.cors import CORSMiddleware
from centeral_marketplace.users.resource import users_router
from centeral_marketplace.products.resource import product_router
from centeral_marketplace.channels.resource import channel_router
from centeral_marketplace.comments.resource import comment_router
from centeral_marketplace.reactions.resource import reaction_router
from centeral_marketplace.sellers.resource import sellers_router
from centeral_marketplace.bookmarks.resource import bookmark_router
from centeral_marketplace.files.resource import files_router
from centeral_marketplace.notifications.resource import notifications_router


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


def create_app(injector: Injector | None = None) -> FastAPI:
    app = FastAPI()
    sub_api = FastAPI()

    origins = ["http://localhost", "http://localhost:3000", "*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    app.mount("/api/v1", sub_api)

    sub_api.include_router(users_router)
    sub_api.include_router(product_router)
    sub_api.include_router(channel_router)
    sub_api.include_router(comment_router)
    sub_api.include_router(reaction_router)
    sub_api.include_router(sellers_router)
    sub_api.include_router(bookmark_router)
    sub_api.include_router(files_router)
    sub_api.include_router(notifications_router)

    if injector is None:
        injector = create_injector()

    @sub_api.get("/health_check")
    async def health_check():
        return {"message": "healthy"}

    attach_injector(app, injector)
    attach_injector(sub_api, injector)

    user_service = injector.get(UserService)
    config = injector.get(Config)

    @app.on_event("startup")
    async def startup_event():
        try:
            user_service.create_admin(
                UserCreate(
                    first_name="Central Marketplace",
                    last_name="Admin",
                    email=config.admin_email,
                    password=config.admin_password,
                )
            )
            logger.info(f"Admin user created with email: {config.admin_email}")
        except Exception as e:
            logger.error(f"Error creating admin user: {e}")

    return app
