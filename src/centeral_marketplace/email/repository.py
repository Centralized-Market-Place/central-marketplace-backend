from centeral_marketplace.email.core import EmailVerificationToken
from config  import Config
from centeral_marketplace.infrastructure.mongo import MongoDBJsonRepositoryDelegate
from injector import inject, singleton
from dataclasses import dataclass


@inject
@singleton
@dataclass
class EmailVerificationTokenRepository:
    config: Config

    def __post_init__(self):
        self.delegate = MongoDBJsonRepositoryDelegate(
            collection_name="email_verification_tokens", model=EmailVerificationToken, config=self.config
        )

    def save_token(self, token: EmailVerificationToken):
        return self.delegate.save(token)

    def get_token(self, token_str: str) -> EmailVerificationToken:
        return self.delegate.find_one_by_dict({"token": token_str})

    def delete_token(self, token_str: str):
        token = self.delegate.find_one_by_dict({"token": token_str})
        if token:
            self.delegate.delete_one(token.id)
