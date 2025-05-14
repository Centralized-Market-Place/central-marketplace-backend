import time
from fastapi.testclient import TestClient
from hamcrest import assert_that, equal_to, has_key

from centeral_marketplace.users.auth import create_access_token
from centeral_marketplace.users.core import Role, User
from tests.core.given import given, then, when
from tests.core.modules import (
    create_test_client,
    prepare_api_server,
    prepare_injector,
)
from tests.steps.database import database_is_clean, database_repo_is_ready
from tests.steps.users import there_is_a_user


def test_get_signed_upload_url_for_png():
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
                role=Role.USER,
            ),
        ]
    ) as context:
        client: TestClient = context.client
        user: User = context.user
        token = create_access_token({"sub": str(user.id)})

        with when("I request a signed upload URL for PNG file"):
            response = client.post(
                "api/v1/files/signed-upload-url",
                headers={"Authorization": f"Bearer {token}"},
                json={"file_type": "png", "folder": "test-uploads"},
            )

            with then("I should receive a valid signed URL response"):
                assert_that(response.status_code, equal_to(200))
                data = response.json()

                # Verify the response structure
                for field in [
                    "signature",
                    "timestamp",
                    "cloud_name",
                    "api_key",
                    "folder",
                    "resource_type",
                ]:
                    assert_that(data, has_key(field))
                assert_that(data["folder"], equal_to("test-uploads"))
                assert_that(data["resource_type"], equal_to("image"))

                # Verify the timestamp is recent (within last minute)
                current_time = int(time.time())
                assert_that(current_time - data["timestamp"] < 60, equal_to(True))


def test_get_signed_upload_url_for_pdf():
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
                role=Role.USER,
            ),
        ]
    ) as context:
        client: TestClient = context.client
        user: User = context.user
        token = create_access_token({"sub": str(user.id)})

        with when("I request a signed upload URL for PDF file"):
            response = client.post(
                "api/v1/files/signed-upload-url",
                headers={"Authorization": f"Bearer {token}"},
                json={"file_type": "pdf", "folder": "documents"},
            )

            with then(
                "I should receive a valid signed URL response for raw resource type"
            ):
                assert_that(response.status_code, equal_to(200))
                data = response.json()

                # Verify the response structure
                for field in [
                    "signature",
                    "timestamp",
                    "cloud_name",
                    "api_key",
                    "folder",
                    "resource_type",
                ]:
                    assert_that(data, has_key(field))
                assert_that(data["folder"], equal_to("documents"))
                assert_that(data["resource_type"], equal_to("raw"))


def test_get_signed_upload_url_unauthorized():
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

        with when("I request a signed upload URL without authentication"):
            response = client.post(
                "api/v1/files/signed-upload-url",
                json={"file_type": "png", "folder": "test-uploads"},
            )

            with then("I should receive an unauthorized error"):
                assert_that(response.status_code, equal_to(401))


def test_get_signed_upload_url_invalid_file_type():
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
                role=Role.USER,
            ),
        ]
    ) as context:
        client: TestClient = context.client
        user: User = context.user
        token = create_access_token({"sub": str(user.id)})

        with when("I request a signed upload URL with invalid file type"):
            response = client.post(
                "api/v1/files/signed-upload-url",
                headers={"Authorization": f"Bearer {token}"},
                json={"file_type": "invalid", "folder": "test-uploads"},
            )

            with then("I should receive a validation error"):
                assert_that(response.status_code, equal_to(422))
                data = response.json()
                assert_that(data["detail"][0]["loc"][1], equal_to("file_type"))
