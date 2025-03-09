from fastapi import FastAPI
from fastapi_injector import attach_injector
from injector import Injector
from utils import create_injector
from fastapi.middleware.cors import CORSMiddleware
from centeral_marketplace.users.resource import users_router
from centeral_marketplace.products.resource import product_router


def create_app(injector: Injector = None) -> FastAPI:
    app = FastAPI()
    sub_api = FastAPI()

    origins = ["http://localhost", "http://localhost:3000", "*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    app.mount("/api/v1", sub_api)

    sub_api.include_router(users_router)
    sub_api.include_router(product_router)

    if injector is None:
        injector = create_injector()

    @sub_api.get("/health_check")
    async def health_check():
        return {"message": "healthy"}

    attach_injector(app, injector)
    attach_injector(sub_api, injector)

    return app
