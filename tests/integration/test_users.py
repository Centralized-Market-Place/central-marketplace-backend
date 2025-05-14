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
                    "first_name": "John",
                    "last_name": "Doe",
                },
            )

            assert_that(response.status_code, equal_to(200))
            data = response.json()
            assert_that(data["email"], equal_to("test@gmail.com"))
            assert_that(data["first_name"], equal_to("John"))
            assert_that(data["last_name"], equal_to("Doe"))
            assert_that("password" not in data)


def test_users_with_same_email_should_not_be_able_to_register():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(first_name="John", last_name="Doe", email="test@gmail.com", password="password"),
        ]
    ) as context:
        client: TestClient = context.client

        with when("i register a user with same email"):
            response = client.post(
                url="api/v1/users/register",
                json={
                    "email": "test@gmail.com",
                    "password": "password",
                    "first_name": "John",
                    "last_name": "Doe",
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
            there_is_a_user(first_name="Test", last_name="User", email="test@gmail.com", password="password"),
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
            there_is_a_user(first_name="Test", last_name="User", email="test@gmail.com", password="password"),
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
            there_is_a_user(first_name="Test", last_name="User", email="test@gmail.com", password="password"),
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
                first_name="Test",
                last_name="User",
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
                first_name="Test",
                last_name="User",
                email="test@gmail.com",
                password="password",
                role=Role.USER
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


def test_user_should_be_able_to_update_personal_info():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(first_name="John", last_name="Doe", email="test@gmail.com", password="password"),
        ]
    ) as context:
        client: TestClient = context.client
        token = create_access_token({"sub": str(context.user.id)})

        with when("i update personal info"):
            response = client.put(
                url="api/v1/users/profile/personal-info",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "date_of_birth": "1990-01-01",
                    "gender": "male",
                    "nationality": "USA",
                    "profile_picture": "https://example.com/photo.jpg",
                    "bio": "Test bio",
                },
            )

            assert_that(response.status_code, equal_to(200))
            data = response.json()
            assert_that(data["personal_info"]["gender"], equal_to("male"))
            assert_that(data["personal_info"]["nationality"], equal_to("USA"))


def test_user_should_be_able_to_update_contact_info():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(first_name="Test", last_name="User", email="test@gmail.com", password="password"),
        ]
    ) as context:
        client: TestClient = context.client
        token = create_access_token({"sub": str(context.user.id)})

        with when("i update contact info"):
            response = client.put(
                url="api/v1/users/profile/contact-info",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "phone_number": "+1234567890",
                    "alternative_email": "alt@example.com",
                },
            )

            assert_that(response.status_code, equal_to(200))
            data = response.json()
            assert_that(data["contact_info"]["phone_number"], equal_to("+1234567890"))
            assert_that(data["contact_info"]["alternative_email"], equal_to("alt@example.com"))


def test_user_should_be_able_to_update_location_info():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(first_name="Test", last_name="User", email="test@gmail.com", password="password"),
        ]
    ) as context:
        client: TestClient = context.client
        token = create_access_token({"sub": str(context.user.id)})

        with when("i update location info"):
            response = client.put(
                url="api/v1/users/profile/location-info",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "country": "USA",
                    "city": "New York",
                    "address": "123 Main St",
                    "postal_code": "10001",
                },
            )

            assert_that(response.status_code, equal_to(200))
            data = response.json()
            assert_that(data["location_info"]["country"], equal_to("USA"))
            assert_that(data["location_info"]["city"], equal_to("New York"))


def test_user_should_be_able_to_update_communication_preferences():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(first_name="Test", last_name="User", email="test@gmail.com", password="password"),
        ]
    ) as context:
        client: TestClient = context.client
        token = create_access_token({"sub": str(context.user.id)})

        with when("i update communication preferences"):
            response = client.put(
                url="api/v1/users/profile/communication-preferences",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "email_notifications": True,
                    "sms_notifications": False,
                    "marketing_emails": True,
                },
            )

            assert_that(response.status_code, equal_to(200))
            data = response.json()
            assert_that(data["communication_preferences"]["email_notifications"], equal_to(True))
            assert_that(data["communication_preferences"]["sms_notifications"], equal_to(False))


def test_user_should_be_able_to_update_privacy_settings():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(first_name="Test", last_name="User", email="test@gmail.com", password="password"),
        ]
    ) as context:
        client: TestClient = context.client
        token = create_access_token({"sub": str(context.user.id)})

        with when("i update privacy settings"):
            response = client.put(
                url="api/v1/users/profile/privacy-settings",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "profile_visibility": "public",
                    "show_email": False,
                    "show_phone": False,
                },
            )

            assert_that(response.status_code, equal_to(200))
            data = response.json()
            assert_that(data["privacy_settings"]["profile_visibility"], equal_to("public"))
            assert_that(data["privacy_settings"]["show_email"], equal_to(False))


def test_user_should_be_able_to_get_profile_completion():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(first_name="Test", last_name="User", email="test@gmail.com", password="password"),
        ]
    ) as context:
        client: TestClient = context.client
        token = create_access_token({"sub": str(context.user.id)})

        with when("i get profile completion"):
            response = client.get(
                url="api/v1/users/profile/completion",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert_that(response.status_code, equal_to(200))
            data = response.json()
            assert_that("completion_percentage" in data)
            assert_that("missing_fields" in data)
