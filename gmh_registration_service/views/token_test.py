from gmh_registration_service.test_utils import (
    environment,
    environment_session,
    insert_token,
)
from gmh_registration_service.messages import (
    INVALID_CREDENTIALS,
    INTERNAL_ERROR,
    BAD_REQUEST,
)

from .token import random_token


async def test_random_token():
    assert len(random_token()) == 64


async def test_supported_method(environment):
    client, _, _, _ = environment
    response = client.get("/token")
    assert response.status_code == 405

    response = client.post("/token")
    assert response.status_code == 400
    assert response.text == BAD_REQUEST


async def test_get_token(environment):
    client, _, _, database = environment

    response = client.post("/token", json={"username": "Bob", "password": "Secret"})
    assert response.status_code == 403
    assert response.text == INVALID_CREDENTIALS

    insert_token(database, token="token")

    response = client.post("/token", content="username: Bob, password: Secret")
    assert response.status_code == 400

    response = client.post("/token", json={"username": "Bob", "password": "Secret"})
    assert response.status_code == 200
    assert len(response.text) == 64


async def test_internal_server_error(environment):
    client, _, _, database = environment

    database.select_query = None

    response = client.post("/token", json={"username": "Bob", "password": "Secret"})
    assert response.status_code == 500
    assert response.text == INTERNAL_ERROR
