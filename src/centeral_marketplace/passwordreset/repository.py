from dataclasses import dataclass
from centeral_marketplace.infrastructure.mongo import MongoDBJsonRepositoryDelegate
from .core import PasswordResetToken
from config import Config
from injector import inject, singleton


@inject
@singleton
@dataclass
class PasswordResetRepository:
    config: Config

    def __post_init__(self):
        self.delegate = MongoDBJsonRepositoryDelegate(
            collection_name="password_reset_tokens",
            model=PasswordResetToken,
            config=self.config,
        )
        self.delegate.ensure_index("token", unique=True)

    def save_token(self, token: PasswordResetToken):
        return self.delegate.save(token)

    def get_token(self, token_str: str) -> PasswordResetToken:
        return self.delegate.find_one_by_dict({"token": token_str})

    def delete_token(self, token_str: str):
        token = self.delegate.find_one_by_dict({"token": token_str})
        if token:
            self.delegate.delete_one(token.id)
