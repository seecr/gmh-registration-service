from gmh_registration_service.test_utils import environment, environment_session
from gmh_registration_service.messages import INVALID_MESSAGE, INTERNAL_ERROR

from .token import random_token


async def test_random_token():
    assert len(random_token()) == 64


async def test_supported_method(environment):
    response = environment.client.get("/token")
    assert response.status_code == 405

    response = environment.client.post("/token")
    assert response.status_code == 401
    assert response.text == INVALID_MESSAGE


async def test_get_token(environment):
    response = environment.client.post(
        "/token", data={"username": "Bob", "password": "Secret"}
    )
    assert response.status_code == 401
    assert response.text == INVALID_MESSAGE

    pool = environment.pool
    with pool.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO registrant (registrant_groupid) VALUES (%(groupid)s)",
                dict(groupid="GROUP_ID"),
            )
            registrant_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO credentials (registrant_id, org_prefix, username, password) VALUES (%(registrant_id)s, %(org_prefix)s, %(username)s, %(password)s)",
                dict(
                    registrant_id=registrant_id,
                    org_prefix="SEECR",
                    username="Bob",
                    password="Secret",
                ),
            )
            conn.commit()

    response = environment.client.post(
        "/token", data={"username": "Bob", "password": "Secret"}
    )
    assert response.status_code == 200
    assert len(response.text) == 64


async def test_internal_server_error(environment):
    environment.pool.get_connection = None
    response = environment.client.post(
        "/token", data={"username": "Bob", "password": "Secret"}
    )
    assert response.status_code == 500
    assert response.text == INTERNAL_ERROR
