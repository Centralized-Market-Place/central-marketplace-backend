import hashlib
import hmac
import time
from centeral_marketplace.users.auth import create_access_token
from config import Config
from fastapi.testclient import TestClient
from hamcrest import assert_that, equal_to
from tests.core.given import given, when
from tests.core.modules import create_test_client, prepare_api_server, prepare_injector
from tests.steps.database import database_is_clean, database_repo_is_ready
from centeral_marketplace.users.core import Role, TelegramLogin

from tests.steps.users import there_is_a_user


def test_users_should_be_able_to_register():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
        ]
    ) as context:
        client: TestClient = context.client

        with when("i register a user"):
            response = client.post(
                url="api/v1/users/register",
                json={
                    "email": "test@gmail.com",
                    "password": "password",
                    "name": "test",
                },
            )

            assert_that(response.status_code, equal_to(200))
            data = response.json()
            assert_that(data["email"], equal_to("test@gmail.com"))
            assert_that(data["name"], equal_to("test"))
            assert_that("password" not in data)


def test_users_with_same_email_should_not_be_able_to_register():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(name="test", email="test@gmail.com", password="password"),
        ]
    ) as context:
        client: TestClient = context.client

        with when("i register a user with same email"):
            response = client.post(
                url="api/v1/users/register",
                json={
                    "email": "test@gmail.com",
                    "password": "password",
                    "name": "test",
                },
            )

            assert_that(response.status_code, equal_to(409))
            data = response.json()
            assert_that(
                data["detail"], equal_to("User with the current email already exist")
            )


def test_users_should_be_able_to_login():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(name="test", email="test@gmail.com", password="password"),
        ]
    ) as context:
        client: TestClient = context.client

        with when("i login a user"):
            response = client.post(
                url="api/v1/users/login",
                json={
                    "email": "test@gmail.com",
                    "password": "password",
                },
            )

            assert_that(response.status_code, equal_to(200))
            data = response.json()
            assert_that("token" in data)
            assert_that(data["user"]["email"], equal_to("test@gmail.com"))


def test_users_should_not_be_able_to_login_with_wrong_password():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(name="test", email="test@gmail.com", password="password"),
        ]
    ) as context:
        client: TestClient = context.client

        with when("i login a user with wrong password"):
            response = client.post(
                url="api/v1/users/login",
                json={
                    "email": "test@gmail.com",
                    "password": "wrongpassword",
                },
            )

            assert_that(response.status_code, equal_to(400))
            data = response.json()
            assert_that(data["detail"], equal_to("Incorrect Email or Password"))


def test_users_should_not_be_able_to_login_with_wrong_email():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(name="test", email="test@gmail.com", password="password"),
        ]
    ) as context:
        client: TestClient = context.client

        with when("i login a user with wrong email"):
            response = client.post(
                url="api/v1/users/login",
                json={
                    "email": "test2@gmail.com",
                    "password": "password",
                },
            )

            assert_that(response.status_code, equal_to(400))
            data = response.json()
            assert_that(data["detail"], equal_to("Incorrect Email or Password"))


def test_admin_should_be_able_to_get_users():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(
                name="test",
                email="test@gmail.com",
                password="password",
                role=Role.ADMIN,
            ),
        ]
    ) as context:
        client: TestClient = context.client
        token = create_access_token({"sub": str(context.user.id)})

        with when("i get users"):
            response = client.get(
                url="api/v1/users",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert_that(response.status_code, equal_to(200))
            data = response.json()
            assert_that(data["total"], equal_to(1))


def test_non_admin_user_should_not_be_able_to_get_users():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(
                name="test", email="test@gmail.com", password="password", role=Role.USER
            ),
        ]
    ) as context:
        client: TestClient = context.client
        token = create_access_token({"sub": str(context.user.id)})

        with when("i get users"):
            response = client.get(
                url="api/v1/users",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert_that(response.status_code, equal_to(403))
            data = response.json()
            assert_that(data["detail"], equal_to("Forbidden"))


def test_register_with_telegram():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
        ]
    ) as context:
        auth_date = time.time() - 1000
        data = TelegramLogin(
            username="Sah7b",
            photo_url="https://t.me/i/userpic/320/6H0rE6lelkP-42qgdKIS3RVuCPeHsIkUcCK3VH67Uz0.jpg",
            id=713289859,
            first_name="Sahib.S",
            auth_date=int(auth_date),
            hash="",
        )

        config: Config = context.injector.get(Config)
        received_data = data.model_dump()
        data_check_arr = []
        received_data.pop("hash")

        for key, value in sorted(received_data.items()):
            if value is not None:
                data_check_arr.append(f"{key}={value}")

        data_check_string = "\n".join(data_check_arr)

        secret_key = hashlib.sha256(config.telegram_bot_token.encode()).digest()

        computed_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()
        data.hash = computed_hash

        client: TestClient = context.client

        with when("i login with telegram"):
            response = client.post(url="api/v1/users/telegram", json=data.model_dump())

            assert_that(response.status_code, equal_to(200))
            data = response.json()
            assert_that("token" in data)
            assert_that(data["user"]["telegram"]["telegram_id"], equal_to(713289859))

        