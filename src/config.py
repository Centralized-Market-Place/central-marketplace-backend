from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Config(BaseSettings):
    mongo_uri: str
    test_mongo_uri: str
    database_name: str
    secret_key: str
    access_token_expires_in: int = 3600 * 24
    jwt_algorithm: str
    telegram_bot_token: str


settings = Config()
