from fastapi import FastAPI
from db import MongoDB

def create_app() -> FastAPI:
    app = FastAPI()

    MongoDB.connect()
    print("MongoDB connected.")

    @app.get("/health_check")
    async def health_check():
        return {"message": "healthy"}

    return app
