import hashlib
import hmac
import time
import pytest
from fastapi.testclient import TestClient
from hamcrest import assert_that, equal_to, has_length, not_none, is_, contains_string

from centeral_marketplace.infrastructure.telegram.service import TelegramService
from centeral_marketplace.users.core import Role, User
from centeral_marketplace.users.auth import create_access_token
from config import Config
from tests.core.given import given, then, when
from tests.core.modules import (
    create_test_client,
    prepare_api_server,
    prepare_injector,
)
from tests.steps.database import database_is_clean, database_repo_is_ready
from tests.steps.users import there_is_a_user


@pytest.mark.ci
def test_telegram_service_is_bot_admin():
    with given(
        [
            prepare_injector(),
        ]
    ) as context:
        telegram_service: TelegramService = context.injector.get(TelegramService)

        with when("I check if the bot is an admin in the channel"):
            result = telegram_service.is_bot_admin("@centeral_marketplace")
            with then("The bot should be an admin in the channel"):
                assert_that(result, equal_to(True))


@pytest.mark.ci
def test_telegram_service_get_chat_administrators():
    with given(
        [
            prepare_injector(),
        ]
    ) as context:
        config: Config = context.injector.get(Config)
        telegram_service: TelegramService = context.injector.get(TelegramService)

        with when("I get the list of administrators from the test channel"):
            response = telegram_service.get_chat_administrators("centeral_marketplace")
            with then("The request should be successful and contain administrators"):
                assert_that(response.ok, equal_to(True))
                assert_that(len(response.result) > 0, equal_to(True))

                bot_found = False
                for admin in response.result:
                    if (
                        admin.get("user", {}).get("username")
                        == config.telegram_bot_username
                    ):
                        bot_found = True
                        break

                assert_that(bot_found, equal_to(True))


@pytest.mark.ci
def test_telegram_service_get_bot_info():
    with given(
        [
            prepare_injector(),
        ]
    ) as context:
        config: Config = context.injector.get(Config)
        telegram_service: TelegramService = context.injector.get(TelegramService)

        with when("I request the bot's information"):
            response = telegram_service.get_bot_info()
            with then("The response should contain valid bot info"):
                assert_that(response.get("ok"), equal_to(True))
                assert_that(
                    response.get("result", {}).get("username"),
                    equal_to(config.telegram_bot_username),
                )


@pytest.mark.ci
def test_telegram_service_get_channel_info():
    with given(
        [
            prepare_injector(),
        ]
    ) as context:
        telegram_service: TelegramService = context.injector.get(TelegramService)

        with when("I request channel information"):
            channel = telegram_service.get_channel_info("centeral_marketplace")

            with then("The channel information should be retrieved successfully"):
                assert_that(channel, not_none())
                assert_that(channel.title, not_none())
                assert_that(channel.username, not_none())
                assert_that(channel.telegram_id, not_none())

                assert_that(channel.username.lower(), equal_to("centeral_marketplace"))
                assert_that(channel.broadcast, equal_to(True))


@pytest.mark.ci
def test_telegram_service_get_channel_info_with_photo():
    with given(
        [
            prepare_injector(),
        ]
    ) as context:
        telegram_service: TelegramService = context.injector.get(TelegramService)

        with when("I request channel information for a channel with photo"):
            channel = telegram_service.get_channel_info("@centeral_marketplace")

            with then("The channel information should include photo URL"):
                assert_that(channel, not_none())

                if channel.thumbnail_url:
                    assert_that(
                        channel.thumbnail_url, contains_string("cloudinary.com")
                    )

                    with when("I try to access the photo URL"):
                        import httpx

                        with httpx.Client() as client:
                            response = client.head(channel.thumbnail_url)
                            with then("The photo URL should be accessible"):
                                assert_that(response.status_code, equal_to(200))


@pytest.mark.ci
def test_seller_apply_endpoint_with_bot_admin_permission():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(
                first_name="Sahib",
                last_name="S",
                email="sahib.s@gmail.com",
                password="password",
                role=Role.USER,
                telegram={
                    "telegram_id": 713289859,
                    "first_name": "Sahib.S",
                    "username": "Sah7b",
                },
            ),
        ]
    ) as context:
        client: TestClient = context.client
        user: User = context.user
        token = create_access_token({"sub": str(user.id)})

        with when("I apply to become a seller"):
            response = client.post(
                "api/v1/sellers/apply",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "business_name": "Test Business",
                    "tin_number": "1234567890",
                    "channel_id": "@centeral_marketplace",
                    "channel_name": "Central Marketplace Test Channel",
                    "government_id": "https://example.com/id.jpg",
                },
            )

            with then("The application should be created successfully"):
                assert_that(response.status_code, equal_to(201))
                data = response.json()
                assert_that(data["status"], equal_to("PENDING"))
                assert_that(
                    data["seller_info"]["business_name"], equal_to("Test Business")
                )
                assert_that(
                    data["seller_info"]["channel_id"], equal_to("@centeral_marketplace")
                )


@pytest.mark.ci
def test_seller_application_review():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(
                first_name="Admin",
                last_name="User",
                email="admin@gmail.com",
                password="password",
                role=Role.ADMIN,
            ),
        ]
    ) as context:
        client: TestClient = context.client
        admin: User = context.user
        admin_token = create_access_token({"sub": str(admin.id)})
        config: Config = context.injector.get(Config)

        with when("I create a user for seller application"):
            user_response = client.post(
                "api/v1/users/register",
                json={
                    "name": "Seller User",
                    "email": "seller@gmail.com",
                    "password": "password",
                },
            )

            auth_date = int(time.time())
            telegram_data = {
                "id": 713289859,
                "first_name": "Seller",
                "username": "selleruser",
                "auth_date": auth_date,
                "hash": "dummy_hash",
            }

            data_check_arr = []
            for key, value in sorted(telegram_data.items()):
                if value is not None and key != "hash":
                    data_check_arr.append(f"{key}={value}")

            data_check_string = "\n".join(data_check_arr)
            secret_key = hashlib.sha256(config.telegram_bot_token.encode()).digest()
            computed_hash = hmac.new(
                secret_key, data_check_string.encode(), hashlib.sha256
            ).hexdigest()

            telegram_data["hash"] = computed_hash

            with when("I login with Telegram"):
                telegram_login_response = client.post(
                    "api/v1/users/telegram", json=telegram_data
                )

            with then("I get the user token"):
                user_token = telegram_login_response.json()["token"]

            with when("I apply to become a seller"):
                application_response = client.post(
                    "api/v1/sellers/apply",
                    headers={"Authorization": f"Bearer {user_token}"},
                    json={
                        "business_name": "Test Business",
                        "tin_number": "1234567890",
                        "channel_id": "@centeral_marketplace",
                        "channel_name": "Central Marketplace Test Channel",
                        "government_id": "https://example.com/id.jpg",
                    },
                )

            with then("The seller application should be created"):
                assert_that(application_response.status_code, equal_to(201))
                application_data = application_response.json()

        with when("Admin reviews and approves the application"):
            review_response = client.post(
                f"api/v1/sellers/applications/{application_data['id']}/review",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "application_id": application_data["id"],
                    "status": "APPROVED",
                    "admin_review_notes": "Application approved",
                },
            )

            with then("The application should be approved"):
                assert_that(review_response.status_code, equal_to(200))
                review_data = review_response.json()
                assert_that(review_data["status"], equal_to("APPROVED"))
                assert_that(
                    review_data["admin_review_notes"], equal_to("Application approved")
                )

            with then("The user should be updated to seller role"):
                user_response = client.get(
                    "api/v1/users/me", headers={"Authorization": f"Bearer {user_token}"}
                )

                user_data = user_response.json()
                assert_that(user_data["role"], equal_to("SELLER"))
                assert_that(user_data["seller_infos"], has_length(1))
                assert_that(
                    user_data["seller_infos"][0]["business_name"],
                    equal_to("Test Business"),
                )


@pytest.mark.ci
def test_check_bot_status_endpoint():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(
                first_name="Sahib",
                last_name="S",
                email="sahib.s@gmail.com",
                password="password",
                role=Role.USER,
                telegram={
                    "telegram_id": 713289859,
                    "first_name": "Sahib.S",
                    "username": "Sah7b",
                },
            ),
        ]
    ) as context:
        client: TestClient = context.client
        user: User = context.user
        token = create_access_token({"sub": str(user.id)})

        with when("I check bot status in the channel"):
            response = client.get(
                "api/v1/sellers/bot-status/@centeral_marketplace",
                headers={"Authorization": f"Bearer {token}"},
            )

            with then("The response should contain bot admin status"):
                assert_that(response.status_code, equal_to(200))
                data = response.json()
                assert_that(data["has_bot_admin_access"], is_(not_none()))
