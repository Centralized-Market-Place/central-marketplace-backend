from bson import ObjectId
from fastapi.testclient import TestClient
from hamcrest import assert_that, equal_to, has_length
from unittest.mock import patch

from centeral_marketplace.sellers.core import SellerApplicationStatus
from centeral_marketplace.channels.repository import ChannelRepository
from centeral_marketplace.users.core import Role, TelegramData, User
from centeral_marketplace.channels.core import Channel
from centeral_marketplace.users.auth import create_access_token
from tests.core.given import given, then, when
from tests.core.modules import (
    create_test_client,
    prepare_api_server,
    prepare_injector,
)
from tests.steps.database import database_is_clean, database_repo_is_ready
from tests.steps.users import there_is_a_user
from tests.steps.sellers import (
    there_is_a_seller_application,
    there_are_multiple_seller_applications,
)
from tests.steps.channels import there_is_a_channel, there_are_multiple_channels
from tests.steps.products import there_are_multiple_products


@patch("centeral_marketplace.sellers.service.TelegramService.verify_channel_ownership")
@patch("centeral_marketplace.sellers.service.TelegramService.is_bot_admin")
def test_user_can_apply_to_become_seller(mock_is_bot_admin, mock_verify_ownership):
    mock_is_bot_admin.return_value = True
    mock_verify_ownership.return_value = True

    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(
                first_name="John",
                last_name="Doe",
                email="user@example.com",
                password="password",
                role=Role.USER,
                telegram=TelegramData(
                    telegram_id=123456789,
                    first_name="John",
                    username="johndoe",
                ),
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
                    "business_name": "John's Electronics",
                    "tin_number": "1234567890",
                    "channel_id": "@johnselectronics",
                    "channel_name": "John's Electronics Channel",
                    "government_id": "https://example.com/id.jpg",
                },
            )

            with then("The application should be created successfully"):
                assert_that(response.status_code, equal_to(201))
                data = response.json()
                assert_that(data["status"], equal_to("PENDING"))
                assert_that(
                    data["seller_info"]["business_name"], equal_to("John's Electronics")
                )
                assert_that(
                    data["seller_info"]["channel_id"], equal_to("@johnselectronics")
                )
                assert_that(data["user_id"], equal_to(str(user.id)))
                mock_is_bot_admin.assert_called_once_with("@johnselectronics")
                mock_verify_ownership.assert_called_once_with(
                    123456789, "@johnselectronics"
                )


def test_user_can_get_own_seller_applications():
    user_id = ObjectId()
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(
                id=user_id,
                first_name="John",
                last_name="Doe",
                email="user@example.com",
                password="password",
                role=Role.USER,
            ),
            there_is_a_seller_application(user_id),
        ]
    ) as context:
        client: TestClient = context.client
        user: User = context.user
        token = create_access_token({"sub": str(user.id)})
        with when("I get my seller applications"):
            response = client.get(
                "api/v1/sellers/applications/me",
                headers={"Authorization": f"Bearer {token}"},
            )

            with then("I should see my applications"):
                assert_that(response.status_code, equal_to(200))
                data = response.json()
                assert_that(data, has_length(1))
                assert_that(data[0]["user_id"], equal_to(str(user.id)))


def test_user_can_get_specific_seller_application():
    user_id = ObjectId()
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(
                id=user_id,
                first_name="John",
                last_name="Doe",
                email="user@example.com",
                password="password",
                role=Role.USER,
            ),
            there_is_a_seller_application(user_id),
        ]
    ) as context:
        client: TestClient = context.client
        user: User = context.user
        token = create_access_token({"sub": str(user.id)})
        with when("I get my specific seller application"):
            with when("I get my specific seller application"):
                response = client.get(
                    f"api/v1/sellers/applications/{context.seller_application.id}",
                    headers={"Authorization": f"Bearer {token}"},
                )

                with then("I should see the application details"):
                    assert_that(response.status_code, equal_to(200))
                    data = response.json()
                    assert_that(
                        data["id"], equal_to(str(context.seller_application.id))
                    )
                    assert_that(data["user_id"], equal_to(str(user.id)))


def test_user_can_update_own_seller_application():
    user_id = ObjectId()
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(
                id=user_id,
                first_name="John",
                last_name="Doe",
                email="user@example.com",
                password="password",
                role=Role.USER,
            ),
            there_is_a_seller_application(user_id),
        ]
    ) as context:
        client: TestClient = context.client
        user: User = context.user
        token = create_access_token({"sub": str(user.id)})
        with when("I update my seller application"):
            with when("I update my seller application"):
                response = client.post(
                    f"api/v1/sellers/applications/{context.seller_application.id}",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "business_name": "Updated Business Name",
                        "tin_number": "9876543210",
                    },
                )

                with then("The application should be updated"):
                    assert_that(response.status_code, equal_to(200))
                    data = response.json()
                    assert_that(
                        data["seller_info"]["business_name"],
                        equal_to("Updated Business Name"),
                    )
                    assert_that(
                        data["seller_info"]["tin_number"], equal_to("9876543210")
                    )


def test_user_can_delete_own_seller_application():
    user_id = ObjectId()
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(
                id=user_id,
                first_name="John",
                last_name="Doe",
                email="user@example.com",
                password="password",
                role=Role.USER,
            ),
            there_is_a_seller_application(user_id),
        ]
    ) as context:
        client: TestClient = context.client
        user: User = context.user
        token = create_access_token({"sub": str(user.id)})
        application_id = context.seller_application.id
        with when("I delete my seller application"):
            with when("I delete my seller application"):
                response = client.delete(
                    f"api/v1/sellers/applications/{application_id}",
                    headers={"Authorization": f"Bearer {token}"},
                )

                with then("The application should be deleted"):
                    assert_that(response.status_code, equal_to(204))

                with when("I try to get the deleted application"):
                    get_response = client.get(
                        f"api/v1/sellers/applications/{application_id}",
                        headers={"Authorization": f"Bearer {token}"},
                    )

                    with then("It should not be found"):
                        assert_that(get_response.status_code, equal_to(404))


def test_admin_can_get_all_seller_applications():
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
                email="admin@example.com",
                password="password",
                role=Role.ADMIN,
            ),
        ]
    ) as context:
        client: TestClient = context.client
        admin: User = context.user
        admin_token = create_access_token({"sub": str(admin.id)})

        user1 = User(
            first_name="User1",
            last_name="Test",
            email="user1@example.com",
            password_hash="hash",
            role=Role.USER,
        )
        user2 = User(
            first_name="User2",
            last_name="Test",
            email="user2@example.com",
            password_hash="hash",
            role=Role.USER,
        )

        applications_data = [
            {
                "user_id": user1.id,
                "business_name": "Business 1",
                "channel_id": "@business1",
                "status": SellerApplicationStatus.PENDING,
            },
            {
                "user_id": user2.id,
                "business_name": "Business 2",
                "channel_id": "@business2",
                "status": SellerApplicationStatus.APPROVED,
            },
        ]
        there_are_multiple_seller_applications(applications_data)(context)
        with when("Admin gets all seller applications"):
            with when("Admin gets all seller applications"):
                response = client.get(
                    "api/v1/sellers/applications",
                    headers={"Authorization": f"Bearer {admin_token}"},
                )

                with then("All applications should be returned"):
                    assert_that(response.status_code, equal_to(200))
                    data = response.json()
                    assert_that(data["total"], equal_to(2))
                    assert_that(data["items"], has_length(2))


def test_admin_can_filter_seller_applications_by_status():
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
                email="admin@example.com",
                password="password",
                role=Role.ADMIN,
            ),
        ]
    ) as context:
        client: TestClient = context.client
        admin: User = context.user
        admin_token = create_access_token({"sub": str(admin.id)})

        user1 = User(
            first_name="User1",
            last_name="Test",
            email="user1@example.com",
            password_hash="hash",
            role=Role.USER,
        )
        user2 = User(
            first_name="User2",
            last_name="Test",
            email="user2@example.com",
            password_hash="hash",
            role=Role.USER,
        )

        applications_data = [
            {
                "user_id": user1.id,
                "business_name": "Pending Business",
                "status": SellerApplicationStatus.PENDING,
            },
            {
                "user_id": user2.id,
                "business_name": "Approved Business",
                "status": SellerApplicationStatus.APPROVED,
            },
        ]
        there_are_multiple_seller_applications(applications_data)(context)
        with when("Admin filters applications by PENDING status"):
            with when("Admin filters applications by PENDING status"):
                response = client.get(
                    "api/v1/sellers/applications?application_status=PENDING",
                    headers={"Authorization": f"Bearer {admin_token}"},
                )

                with then("Only pending applications should be returned"):
                    assert_that(response.status_code, equal_to(200))
                    data = response.json()
                    assert_that(data["total"], equal_to(1))
                    assert_that(data["items"][0]["status"], equal_to("PENDING"))


@patch("centeral_marketplace.sellers.service.TelegramService.get_channel_info")
def test_admin_can_review_seller_application(mock_get_channel_info):
    mock_channel = Channel(
        title="Test Channel",
        username="test_channel",
        telegram_id=103480192384,
        verified=False,
        broadcast=True,
    )
    mock_get_channel_info.return_value = mock_channel
    user_id = ObjectId()

    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(
                id=user_id,
                first_name="Seller",
                last_name="User",
                email="seller@example.com",
                password="password",
                role=Role.USER,
            ),
            there_is_a_user(
                first_name="Admin",
                last_name="User",
                email="admin@example.com",
                password="password",
                role=Role.ADMIN,
            ),
        ]
    ) as context:
        client: TestClient = context.client
        admin: User = context.user
        admin_token = create_access_token({"sub": str(admin.id)})

        there_is_a_seller_application(user_id)(context)
        with when("I get the application id"):
            application_id = context.seller_application.id

            with when("Admin reviews and approves the application"):
                response = client.post(
                    f"api/v1/sellers/applications/{application_id}/review",
                    headers={"Authorization": f"Bearer {admin_token}"},
                    json={
                        "application_id": str(application_id),
                        "status": "APPROVED",
                        "admin_review_notes": "Application looks good",
                    },
                )

                with then("The application should be approved"):
                    assert_that(response.status_code, equal_to(200))
                    data = response.json()
                    assert_that(data["status"], equal_to("APPROVED"))
                    assert_that(
                        data["admin_review_notes"], equal_to("Application looks good")
                    )
                    mock_get_channel_info.assert_called_once_with("@test_channel")


def test_admin_can_reject_seller_application():
    user_id = ObjectId()
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(
                id=user_id,
                first_name="Seller",
                last_name="User",
                email="seller@example.com",
                password="password",
                role=Role.USER,
            ),
            there_is_a_user(
                first_name="Admin",
                last_name="User",
                email="admin@example.com",
                password="password",
                role=Role.ADMIN,
            ),
            there_is_a_seller_application(user_id),
        ]
    ) as context:
        client: TestClient = context.client
        admin: User = context.user
        admin_token = create_access_token({"sub": str(admin.id)})

        with when("I get the application id"):
            application_id = context.seller_application.id

            with when("Admin reviews and rejects the application"):
                response = client.post(
                    f"api/v1/sellers/applications/{application_id}/review",
                    headers={"Authorization": f"Bearer {admin_token}"},
                    json={
                        "application_id": str(application_id),
                        "status": "REJECTED",
                        "admin_review_notes": "Missing required documents",
                    },
                )

                with then("The application should be rejected"):
                    assert_that(response.status_code, equal_to(200))
                    data = response.json()
                    assert_that(data["status"], equal_to("REJECTED"))
                    assert_that(
                        data["admin_review_notes"],
                        equal_to("Missing required documents"),
                    )


def test_non_admin_cannot_get_all_seller_applications():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(
                first_name="Regular",
                last_name="User",
                email="user@example.com",
                password="password",
                role=Role.USER,
            ),
        ]
    ) as context:
        client: TestClient = context.client
        user: User = context.user
        token = create_access_token({"sub": str(user.id)})

        with when("Regular user tries to get all seller applications"):
            response = client.get(
                "api/v1/sellers/applications",
                headers={"Authorization": f"Bearer {token}"},
            )

            with then("Access should be forbidden"):
                assert_that(response.status_code, equal_to(403))


def test_non_admin_cannot_review_seller_application():
    user_id = ObjectId()
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(
                id=user_id,
                first_name="Regular",
                last_name="User",
                email="user@example.com",
                password="password",
                role=Role.USER,
            ),
            there_is_a_seller_application(user_id),
        ]
    ) as context:
        client: TestClient = context.client
        user: User = context.user
        token = create_access_token({"sub": str(user.id)})

        with when("I get the application id"):
            application_id = context.seller_application.id

            with when("Regular user tries to review an application"):
                response = client.post(
                    f"api/v1/sellers/applications/{application_id}/review",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "application_id": str(application_id),
                        "status": "APPROVED",
                        "admin_review_notes": "Unauthorized review",
                    },
                )

                with then("Access should be forbidden"):
                    assert_that(response.status_code, equal_to(403))


def test_user_cannot_view_other_users_applications():
    user_id1 = ObjectId()
    user_id2 = ObjectId()
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(
                id=user_id1,
                first_name="User1",
                last_name="Test",
                email="user1@example.com",
                password="password",
                role=Role.USER,
            ),
            there_is_a_user(
                id=user_id2,
                first_name="User2",
                last_name="Test",
                email="user2@example.com",
                password="password",
                role=Role.USER,
            ),
            there_is_a_seller_application(user_id1),
        ]
    ) as context:
        client: TestClient = context.client
        user1: User = context.user
        user1_token = create_access_token({"sub": str(user1.id)})

        with when("I get the application id"):
            application_id = context.seller_application.id

            with when("User1 tries to view User2's application"):
                response = client.get(
                    f"api/v1/sellers/applications/{application_id}",
                    headers={"Authorization": f"Bearer {user1_token}"},
                )

                with then("Access should be forbidden"):
                    assert_that(response.status_code, equal_to(403))


@patch("centeral_marketplace.sellers.service.TelegramService.verify_channel_ownership")
@patch("centeral_marketplace.sellers.service.TelegramService.is_bot_admin")
def test_check_bot_status_endpoint(mock_is_bot_admin, mock_verify_ownership):
    mock_is_bot_admin.return_value = True
    mock_verify_ownership.return_value = True

    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(
                first_name="John",
                last_name="Doe",
                email="user@example.com",
                password="password",
                role=Role.USER,
                telegram=TelegramData(
                    telegram_id=123456789,
                    first_name="John",
                    username="johndoe",
                ),
            ),
        ]
    ) as context:
        client: TestClient = context.client
        user: User = context.user
        token = create_access_token({"sub": str(user.id)})

        with when("I check bot status for a channel"):
            response = client.get(
                "api/v1/sellers/bot-status/@testchannel",
                headers={"Authorization": f"Bearer {token}"},
            )

            with then("Bot status should be returned"):
                assert_that(response.status_code, equal_to(200))
                data = response.json()
                assert_that("has_bot_admin_access" in data)
                assert_that("verified_channel_ownership" in data)
                assert_that(data["has_bot_admin_access"], equal_to(True))
                assert_that(data["verified_channel_ownership"], equal_to(True))

                mock_is_bot_admin.assert_called_once_with("@testchannel")
                mock_verify_ownership.assert_called_once_with(123456789, "@testchannel")


def test_seller_analytics_endpoint():
    user_id = ObjectId()
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(
                id=user_id,
                first_name="Seller",
                last_name="User",
                email="seller@example.com",
                password="password",
                role=Role.SELLER,
            ),
        ]
    ) as context:
        channel1_data = {
            "telegram_id": 111111111,
            "title": "Electronics Store",
            "username": "electronics_store",
            "description": "Best electronics",
        }
        channel2_data = {
            "telegram_id": 222222222,
            "title": "Fashion Store",
            "username": "fashion_store",
            "description": "Latest fashion",
        }

        there_are_multiple_channels([channel1_data, channel2_data])(context)

        there_is_a_seller_application(
            user_id,
            business_name="Electronics Business",
            channel_id="electronics_store",
            channel_name="Electronics Store",
            status=SellerApplicationStatus.APPROVED,
        )(context)

        there_is_a_seller_application(
            user_id,
            business_name="Fashion Business",
            channel_id="fashion_store",
            channel_name="Fashion Store",
            status=SellerApplicationStatus.APPROVED,
        )(context)

        channel_repo = context.injector.get(ChannelRepository)

        electronics_channel = channel_repo.find_one_by_dict(
            {"username": "electronics_store"}
        )
        fashion_channel = channel_repo.find_one_by_dict({"username": "fashion_store"})

        electronics_products = [
            {
                "channel_id": electronics_channel.id,
                "telegram_channel_id": 111111111,
                "title": "Laptop",
                "price": 150.0,
                "views": 100,
                "is_available": True,
            },
            {
                "channel_id": electronics_channel.id,
                "telegram_channel_id": 111111111,
                "title": "Phone",
                "price": 200.0,
                "views": 200,
                "is_available": True,
            },
            {
                "channel_id": electronics_channel.id,
                "telegram_channel_id": 111111111,
                "title": "Tablet",
                "price": 300.0,
                "views": 50,
                "is_available": False,
            },
        ]

        fashion_products = [
            {
                "channel_id": fashion_channel.id,
                "telegram_channel_id": 222222222,
                "title": "T-Shirt",
                "price": 50.0,
                "views": 80,
                "is_available": True,
            },
            {
                "channel_id": fashion_channel.id,
                "telegram_channel_id": 222222222,
                "title": "Jeans",
                "price": 75.0,
                "views": 120,
                "is_available": True,
            },
        ]

        there_are_multiple_products(electronics_products + fashion_products)(context)

        client: TestClient = context.client
        seller: User = context.user
        token = create_access_token({"sub": str(seller.id)})

        with when("I get seller analytics"):
            response = client.get(
                "api/v1/sellers/analytics",
                headers={"Authorization": f"Bearer {token}"},
            )

            with then("Analytics should be returned with correct calculations"):
                assert_that(response.status_code, equal_to(200))
                data = response.json()

                assert_that(data["total_channels"], equal_to(2))
                assert_that(data["total_products"], equal_to(5))
                assert_that(data["total_views"], equal_to(550))
                expected_avg_price = (150.0 + 200.0 + 300.0 + 50.0 + 75.0) / 5
                assert_that(data["average_price"], equal_to(expected_avg_price))
                expected_availability = (4 / 5) * 100
                assert_that(
                    data["availability_percentage"], equal_to(expected_availability)
                )


def test_non_seller_cannot_access_analytics():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(
                first_name="Regular",
                last_name="User",
                email="user@example.com",
                password="password",
                role=Role.USER,
            ),
        ]
    ) as context:
        client: TestClient = context.client
        user: User = context.user
        token = create_access_token({"sub": str(user.id)})

        with when("Regular user tries to access seller analytics"):
            response = client.get(
                "api/v1/sellers/analytics",
                headers={"Authorization": f"Bearer {token}"},
            )

            with then("Access should be forbidden"):
                assert_that(response.status_code, equal_to(403))


@patch("centeral_marketplace.sellers.service.TelegramService.verify_channel_ownership")
@patch("centeral_marketplace.sellers.service.TelegramService.is_bot_admin")
def test_user_cannot_apply_without_bot_admin_access(
    mock_is_bot_admin, mock_verify_ownership
):
    mock_is_bot_admin.return_value = False
    mock_verify_ownership.return_value = True

    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(
                first_name="John",
                last_name="Doe",
                email="user@example.com",
                password="password",
                role=Role.USER,
                telegram=TelegramData(
                    telegram_id=123456789,
                    first_name="John",
                    username="johndoe",
                ),
            ),
        ]
    ) as context:
        client: TestClient = context.client
        user: User = context.user
        token = create_access_token({"sub": str(user.id)})

        with when("I apply to become a seller without bot admin access"):
            response = client.post(
                "api/v1/sellers/apply",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "business_name": "John's Electronics",
                    "tin_number": "1234567890",
                    "channel_id": "@johnselectronics",
                    "channel_name": "John's Electronics Channel",
                    "government_id": "https://example.com/id.jpg",
                },
            )

            with then("The application should be rejected"):
                assert_that(response.status_code, equal_to(400))
                data = response.json()
                assert_that(
                    data["detail"],
                    equal_to("Bot is not added as an admin to the channel"),
                )


@patch("centeral_marketplace.sellers.service.TelegramService.verify_channel_ownership")
@patch("centeral_marketplace.sellers.service.TelegramService.is_bot_admin")
def test_user_cannot_apply_without_channel_ownership(
    mock_is_bot_admin, mock_verify_ownership
):
    # Mock telegram service to return user is not channel owner
    mock_is_bot_admin.return_value = True
    mock_verify_ownership.return_value = False

    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(
                first_name="John",
                last_name="Doe",
                email="user@example.com",
                password="password",
                role=Role.USER,
                telegram=TelegramData(
                    telegram_id=123456789,
                    first_name="John",
                    username="johndoe",
                ),
            ),
        ]
    ) as context:
        client: TestClient = context.client
        user: User = context.user
        token = create_access_token({"sub": str(user.id)})

        with when("I apply to become a seller without channel ownership"):
            response = client.post(
                "api/v1/sellers/apply",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "business_name": "John's Electronics",
                    "tin_number": "1234567890",
                    "channel_id": "@johnselectronics",
                    "channel_name": "John's Electronics Channel",
                    "government_id": "https://example.com/id.jpg",
                },
            )

            with then("The application should be rejected"):
                assert_that(response.status_code, equal_to(400))
                data = response.json()
                assert_that(
                    data["detail"], equal_to("User is not the owner of the channel")
                )
