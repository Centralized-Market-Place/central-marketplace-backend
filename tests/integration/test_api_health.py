from hamcrest import assert_that, equal_to
from starlette.testclient import TestClient

from tests.core.given import given, then, when
from tests.core.modules import create_test_client, prepare_api_server, prepare_injector
from tests.steps.database import database_is_clean, database_repo_is_ready


def test_api_health_is_ok():
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

        with when("i request api health check"):
            response = client.get(url="/health_check")

            with then("status should be OK"):
                data = response.json()
                assert_that(response.status_code, equal_to(200))
                assert_that(data, equal_to({"message": "healthy"}))
