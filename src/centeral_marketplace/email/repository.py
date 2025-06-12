from centeral_marketplace.email.core import EmailVerificationToken
from config import Config
from centeral_marketplace.infrastructure.mongo import MongoDBJsonRepositoryDelegate
from injector import inject, singleton
from dataclasses import dataclass
from typing import List
from core import PyObjectId


@inject
@singleton
@dataclass
class EmailVerificationTokenRepository:
    config: Config

    def __post_init__(self):
        self.delegate = MongoDBJsonRepositoryDelegate(
            collection_name="email_verification_tokens",
            model=EmailVerificationToken,
            config=self.config,
        )

    def save_token(self, token: EmailVerificationToken):
        return self.delegate.save(token)

    def get_token(self, token_str: str) -> EmailVerificationToken:
        return self.delegate.find_one_by_dict({"token": token_str})

    def delete_token(self, token_str: str):
        token = self.delegate.find_one_by_dict({"token": token_str})
        if token:
            self.delegate.delete_one(token.id)

    def delete_tokens_for_user(self, user_id: PyObjectId) -> int:
        tokens = self.delegate.find_all_by_dict({"user_id": user_id})
        deleted_count = 0

        for token in tokens:
            self.delegate.delete_one(token.id)
            deleted_count += 1

        return deleted_count

    def get_tokens_for_user(self, user_id: PyObjectId) -> List[EmailVerificationToken]:
        return self.delegate.find_all_by_dict({"user_id": user_id})
