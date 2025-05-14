from fastapi.testclient import TestClient
from hamcrest import (
    assert_that,
    equal_to,
    contains_string,
    has_length,
    greater_than,
    none,
    is_not,
)
from centeral_marketplace.notifications.core import NotificationType
from centeral_marketplace.users.auth import create_access_token
from centeral_marketplace.users.core import User

from tests.core.given import given, when, then
from tests.core.modules import create_test_client, prepare_api_server, prepare_injector
from tests.steps.database import database_is_clean, database_repo_is_ready
from tests.steps.users import there_is_a_user
from tests.steps.notifications import (
    there_is_a_notification,
    there_are_multiple_notifications,
)


def test_user_can_list_notifications():
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
                email="user@example.com",
                password="password",
            ),
            there_are_multiple_notifications(count=10),
        ]
    ) as context:
        client: TestClient = context.client
        user: User = context.user
        token = create_access_token({"sub": str(user.id)})

        with when("user requests their notifications"):
            response = client.get(
                url="api/v1/notifications", headers={"Authorization": f"Bearer {token}"}
            )

            with then("response should be successful"):
                assert_that(response.status_code, equal_to(200))

            with then("response should contain paginated notifications"):
                data = response.json()
                assert_that(data["total"], equal_to(10))
                assert_that(data["page"], equal_to(1))
                assert_that(data["page_size"], equal_to(20))
                assert_that(len(data["items"]), equal_to(10))

                # Verify first item
                first_item = data["items"][0]
                assert_that(first_item["user_id"], equal_to(str(user.id)))
                assert_that(
                    first_item["notification_type"],
                    equal_to(NotificationType.SYSTEM.value),
                )


def test_user_can_filter_notifications_by_read_status():
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
                email="user@example.com",
                password="password",
            ),
            there_are_multiple_notifications(count=10),
        ]
    ) as context:
        client: TestClient = context.client
        user: User = context.user
        token = create_access_token({"sub": str(user.id)})
        read_count = context.read_notifications_count

        with when("user requests only read notifications"):
            response = client.get(
                url="api/v1/notifications?read=true",
                headers={"Authorization": f"Bearer {token}"},
            )

            with then("response should only contain read notifications"):
                data = response.json()
                assert_that(data["total"], equal_to(read_count))
                assert_that(len(data["items"]), equal_to(read_count))

                # Verify all returned items are read
                for item in data["items"]:
                    assert_that(item["read"], equal_to(True))

        with when("user requests only unread notifications"):
            response = client.get(
                url="api/v1/notifications?read=false",
                headers={"Authorization": f"Bearer {token}"},
            )

            with then("response should only contain unread notifications"):
                data = response.json()
                assert_that(data["total"], equal_to(context.unread_notifications_count))

                # Verify all returned items are unread
                for item in data["items"]:
                    assert_that(item["read"], equal_to(False))


def test_user_can_mark_notification_as_read():
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
                email="user@example.com",
                password="password",
            ),
            there_is_a_notification(read=False),
        ]
    ) as context:
        client: TestClient = context.client
        user: User = context.user
        token = create_access_token({"sub": str(user.id)})
        notification = context.notification

        with when("user marks a notification as read"):
            response = client.post(
                url=f"api/v1/notifications/{notification.id}/read",
                headers={"Authorization": f"Bearer {token}"},
            )

            with then("notification should be marked as read"):
                assert_that(response.status_code, equal_to(200))
                data = response.json()
                assert_that(data["id"], equal_to(str(notification.id)))
                assert_that(data["read"], equal_to(True))
                assert_that(data["read_at"], is_not(none()))

        with when("user marks the same notification as read again"):
            response = client.post(
                url=f"api/v1/notifications/{notification.id}/read",
                headers={"Authorization": f"Bearer {token}"},
            )

            with then("operation should succeed with no errors"):
                assert_that(response.status_code, equal_to(200))
                data = response.json()
                assert_that(data["read"], equal_to(True))


def test_user_cannot_mark_other_users_notification_as_read():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(
                first_name="User1",
                last_name="Test",
                email="user1@example.com",
                password="password",
            ),
            there_is_a_notification(read=False),
            there_is_a_user(
                first_name="User2",
                last_name="Test",
                email="user2@example.com",
                password="password",
            ),
        ]
    ) as context:
        client: TestClient = context.client
        notification = context.notification
        user2: User = context.user
        token = create_access_token({"sub": str(user2.id)})

        with when("User2 tries to mark User1's notification as read"):
            response = client.post(
                url=f"api/v1/notifications/{notification.id}/read",
                headers={"Authorization": f"Bearer {token}"},
            )

            with then("request should be forbidden"):
                assert_that(response.status_code, equal_to(403))
                data = response.json()
                assert_that(data["detail"], contains_string("Not authorized"))


def test_user_can_delete_notification():
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
                email="user@example.com",
                password="password",
            ),
            there_is_a_notification(),
        ]
    ) as context:
        client: TestClient = context.client
        user: User = context.user
        token = create_access_token({"sub": str(user.id)})
        notification = context.notification

        with when("user deletes a notification"):
            response = client.delete(
                url=f"api/v1/notifications/{notification.id}",
                headers={"Authorization": f"Bearer {token}"},
            )

            with then("notification should be deleted"):
                assert_that(response.status_code, equal_to(204))

        with when("user tries to access the deleted notification"):
            response = client.post(
                url=f"api/v1/notifications/{notification.id}/read",
                headers={"Authorization": f"Bearer {token}"},
            )

            with then("notification should no longer exist"):
                assert_that(response.status_code, equal_to(404))


def test_user_cannot_delete_other_users_notification():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(
                first_name="User1",
                last_name="Test",
                email="user1@example.com",
                password="password",
            ),
            there_is_a_notification(),
            there_is_a_user(
                first_name="User2",
                last_name="Test",
                email="user2@example.com",
                password="password",
            ),
        ]
    ) as context:
        client: TestClient = context.client
        notification = context.notification  # This belongs to User1
        user2: User = context.user  # Now context.user is User2
        token = create_access_token({"sub": str(user2.id)})

        with when("User2 tries to delete User1's notification"):
            response = client.delete(
                url=f"api/v1/notifications/{notification.id}",
                headers={"Authorization": f"Bearer {token}"},
            )

            with then("request should be forbidden"):
                assert_that(response.status_code, equal_to(403))


def test_user_can_delete_all_notifications():
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
                email="user@example.com",
                password="password",
            ),
            there_are_multiple_notifications(count=10),
        ]
    ) as context:
        client: TestClient = context.client
        user: User = context.user
        token = create_access_token({"sub": str(user.id)})

        with when("user lists their notifications before deletion"):
            pre_response = client.get(
                url="api/v1/notifications", headers={"Authorization": f"Bearer {token}"}
            )

            with then("user should have notifications"):
                pre_data = pre_response.json()
                assert_that(pre_data["total"], greater_than(0))

        with when("user deletes all their notifications"):
            delete_response = client.delete(
                url="api/v1/notifications", headers={"Authorization": f"Bearer {token}"}
            )

            with then("deletion should be successful"):
                assert_that(delete_response.status_code, equal_to(204))

        with when("user lists their notifications after deletion"):
            post_response = client.get(
                url="api/v1/notifications", headers={"Authorization": f"Bearer {token}"}
            )

            with then("user should have no notifications"):
                post_data = post_response.json()
                assert_that(post_data["total"], equal_to(0))
                assert_that(post_data["items"], has_length(0))


def test_pagination_works_for_notifications():
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
                email="user@example.com",
                password="password",
            ),
            there_are_multiple_notifications(
                count=25
            ),  # Create more than default page size
        ]
    ) as context:
        client: TestClient = context.client
        user: User = context.user
        token = create_access_token({"sub": str(user.id)})

        with when("user requests first page with custom page size"):
            response = client.get(
                url="api/v1/notifications?page=1&page_size=10",
                headers={"Authorization": f"Bearer {token}"},
            )

            with then("first page should contain correct number of items"):
                data = response.json()
                assert_that(data["total"], equal_to(25))
                assert_that(data["page"], equal_to(1))
                assert_that(data["page_size"], equal_to(10))
                assert_that(len(data["items"]), equal_to(10))

        with when("user requests second page"):
            response = client.get(
                url="api/v1/notifications?page=2&page_size=10",
                headers={"Authorization": f"Bearer {token}"},
            )

            with then("second page should contain correct number of items"):
                data = response.json()
                assert_that(data["page"], equal_to(2))
                assert_that(len(data["items"]), equal_to(10))

        with when("user requests third page"):
            response = client.get(
                url="api/v1/notifications?page=3&page_size=10",
                headers={"Authorization": f"Bearer {token}"},
            )

            with then("third page should contain remaining items"):
                data = response.json()
                assert_that(data["page"], equal_to(3))
                assert_that(len(data["items"]), equal_to(5))


def test_authentication_required_for_notification_endpoints():
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
                email="user@example.com",
                password="password",
            ),
            there_is_a_notification(),
        ]
    ) as context:
        client: TestClient = context.client
        notification = context.notification

        endpoints = [
            ("GET", "api/v1/notifications"),
            ("POST", f"api/v1/notifications/{notification.id}/read"),
            ("DELETE", f"api/v1/notifications/{notification.id}"),
            ("DELETE", "api/v1/notifications"),
        ]

        for method, url in endpoints:
            with when(f"unauthenticated user accesses {method} {url}"):
                if method == "GET":
                    response = client.get(url)
                elif method == "POST":
                    response = client.post(url)
                elif method == "DELETE":
                    response = client.delete(url)

                with then("access should be denied"):
                    assert_that(response.status_code, equal_to(401))
