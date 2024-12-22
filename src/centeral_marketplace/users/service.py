

from dataclasses import dataclass
from injector import inject, singleton

from centeral_marketplace.users.repository import UserRepository


@singleton
@inject
@dataclass
class UserService:

    user_repository: UserRepository

    def find_all(self):
        return self.user_repository.find_all()