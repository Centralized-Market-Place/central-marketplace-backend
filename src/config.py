from functools import lru_cache
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
    telegram_bot_username: str
    admin_email: str
    admin_password: str
    redis_url: str
    test_telegram_bot_token: str
    test_telegram_bot_username: str
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    brevo_api_key: str
    email_from: str


    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_config():
    return Config()


settings = get_config()
