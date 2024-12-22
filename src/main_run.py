import uvicorn
from fastapi import FastAPI

from app import create_app

app: FastAPI = create_app()

if __name__ == "__main__":
    uvicorn.run("main_run:app", host="0.0.0.0", port=8443, reload=True)
