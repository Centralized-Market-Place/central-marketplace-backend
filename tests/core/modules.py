from typing import TypeVar
from app import create_app
from config import Config
from injector import Injector
from starlette.testclient import TestClient
from utils import create_modules


def prepare_injector(modules=None):
    def step(context):
        mod_default = create_modules()
        modules_final = mod_default + (modules or [])
        context.injector = Injector(modules=modules_final)
        config: Config = context.injector.get(Config)
        config.mongo_uri = config.mongo_uri
        config.telegram_bot_token = config.test_telegram_bot_token
        config.telegram_bot_username = config.test_telegram_bot_username

    return step


def prepare_api_server():
    def step(context):
        context.app = create_app(context.injector)

    return step


def create_test_client():
    def step(context):
        app = context.app
        context.client = TestClient(app)

    return step


C = TypeVar("C")
