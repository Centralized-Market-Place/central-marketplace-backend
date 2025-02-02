

from centeral_marketplace.users.auth import create_access_token
from fastapi.testclient import TestClient
from hamcrest import assert_that, equal_to
from tests.core.given import given, when
from tests.core.modules import create_test_client, prepare_api_server, prepare_injector
from tests.steps.database import database_is_clean, database_repo_is_ready
from centeral_marketplace.users.core import Role

from tests.steps.users import there_is_a_user


def test_users_should_be_able_to_register():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean()
        ]
    ) as context:
        client: TestClient = context.client

        with when("i register a user"):
            response = client.post(
                url="/users/register",
                json={
                    "email": "test@gmail.com",
                    "password": "password",
                    "name": "test",
                },)
            
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
            there_is_a_user(name="test", email="test@gmail.com", password="password")
        ]
    ) as context:
        
        client: TestClient = context.client

        with when("i register a user with same email"):
            response = client.post(
                url="/users/register",
                json={
                    "email": "test@gmail.com",
                    "password": "password",
                    "name": "test",
                },)
            
            assert_that(response.status_code, equal_to(409))
            data = response.json()
            assert_that(data["detail"], equal_to("User with the current email already exist"))



def test_users_should_be_able_to_login():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(name="test", email="test@gmail.com", password="password")
        ]
    ) as context:
        client: TestClient = context.client
        
        with when("i login a user"):
            response = client.post(
                url="/users/login",
                json={
                    "email": "test@gmail.com",
                    "password": "password",
                },
            )

            assert_that(response.status_code, equal_to(200))
            data = response.json()
            assert_that("token" in data)
            assert_that(data["email"], equal_to("test@gmail.com"))

def test_users_should_not_be_able_to_login_with_wrong_password():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(name="test", email="test@gmail.com", password="password")
        ]
    ) as context:
        
        client: TestClient = context.client

        with when("i login a user with wrong password"):
            response = client.post(
                url="/users/login",
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
            there_is_a_user(name="test", email="test@gmail.com", password="password")
        ]
    ) as context:
        
        client: TestClient = context.client

        with when("i login a user with wrong email"):
            response = client.post(
                url="/users/login",
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
            there_is_a_user(name="test", email="test@gmail.com", password="password", role=Role.ADMIN)
        ]
    ) as context:
        
        client: TestClient = context.client
        token = create_access_token({"sub" : context.user.id})

        with when("i get users"):
            response = client.get(
                url="/users",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert_that(response.status_code, equal_to(200))
            data = response.json()
            assert_that(data["data"]["total"], equal_to(1))


def test_non_admin_user_should_not_be_able_to_get_users():
    with given(
        [
            prepare_injector(),
            prepare_api_server(),
            create_test_client(),
            database_repo_is_ready(),
            database_is_clean(),
            there_is_a_user(name="test", email="test@gmail.com", password="password", role=Role.USER)
        ]
    ) as context:
        
        client: TestClient = context.client
        token = create_access_token({"sub" : context.user.id})

        with when("i get users"):
            response = client.get(
                url="/users",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert_that(response.status_code, equal_to(403))
            data = response.json()
            assert_that(data["detail"], equal_to("Forbidden"))
            
