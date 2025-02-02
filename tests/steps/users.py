
from centeral_marketplace.users.core import Role, User
from centeral_marketplace.users.repository import UserRepository
from centeral_marketplace.users.auth import hash_password


def there_is_a_user(name: str, email: str, password: str, role: Role = Role.USER):

    def step(context):
        user_repo: UserRepository = context.injector.get(UserRepository)
        password_hash = hash_password(password)
        user = User(name=name, email=email, password_hash=password_hash, role=role)
        user_repo.save(user)
        context.user = user

    return step
