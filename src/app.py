from fastapi import FastAPI
from fastapi_injector import attach_injector

from config import Config
from utils import create_injector
from centeral_marketplace.users.resource import users_router

def create_app() -> FastAPI:
    app = FastAPI()

    app.include_router(users_router)
    injector = create_injector()

    @app.get("/health_check")
    async def health_check():
        return {"message": "healthy"}
    
    attach_injector(app, injector)

    return app
