from bson import ObjectId
from centeral_marketplace.users.core import Role, TelegramData, User
from centeral_marketplace.users.repository import UserRepository
from centeral_marketplace.users.auth import hash_password
from core import PyObjectId


def there_is_a_user(
    last_name: str,
    email: str,
    password: str,
    first_name: str,
    role: Role = Role.USER,
    id: PyObjectId | None = None,
    telegram: TelegramData | None = None,
):
    def step(context):
        user_id = id if id else ObjectId()
        user_repo: UserRepository = context.injector.get(UserRepository)
        password_hash = hash_password(password)
        user = User(
            id=user_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=password_hash,
            role=role,
            telegram=telegram,
        )
        user_repo.save(user)
        context.user = user

    return step
