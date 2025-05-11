from dataclasses import dataclass

from centeral_marketplace.comments.repository import CommentRepository
from centeral_marketplace.reactions.repository import ReactionRepository
from centeral_marketplace.sellers.repository import SellerApplicationRepository

from tests.core.given import LambdaWith
from centeral_marketplace.products.repository import ProductRepository
from centeral_marketplace.users.repository import UserRepository
from centeral_marketplace.notifications.repository import NotificationRepository


@dataclass()
class CompositeCloseable:
    children: list

    def delete_all(self):
        for child in self.children:
            child.delete_all()


def database_repo_is_ready():
    def step(context):
        def open():
            repos_list = [
                UserRepository,
                ProductRepository,
                CommentRepository,
                ReactionRepository,
                SellerApplicationRepository,
                NotificationRepository,
            ]

            def get_repo(repo_name):
                repo = context.injector.get(repo_name)
                return repo

            context.repos = CompositeCloseable([get_repo(repo) for repo in repos_list])

        def close():
            pass

        return LambdaWith(open, close)

    return step


def database_is_clean():
    def step(context):
        context.repos.delete_all()

    return step
