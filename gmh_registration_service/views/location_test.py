from gmh_registration_service.test_utils import environment, environment_session
from gmh_registration_service.messages import INVALID_MESSAGE, NOT_FOUND

from urllib.parse import quote


async def test_no_auth(environment):
    response = environment.client.get("/location/some_location")
    assert response.status_code == 401
    assert response.text == INVALID_MESSAGE
    assert "WWW-Authenticate" in response.headers
    assert response.headers.get("WWW-Authenticate") == "Bearer"


async def test_bad_auth(environment):
    response = environment.client.get(
        "/location/some_location", headers={"Authorization": "Basic 1234"}
    )
    assert response.status_code == 401
    assert response.text == INVALID_MESSAGE
    assert "WWW-Authenticate" in response.headers
    assert response.headers.get("WWW-Authenticate") == "Bearer"

    response = environment.client.get(
        "/location/some_location", headers={"Authorization": "Bearer SOME_TOKEN"}
    )
    assert response.status_code == 401
    assert response.text == INVALID_MESSAGE
    assert "WWW-Authenticate" in response.headers
    assert response.headers.get("WWW-Authenticate") == "Bearer"


async def test_not_found(environment):
    TOKEN = "THE_SECRET_TOKEN"

    pool = environment.pool
    with pool.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO registrant (registrant_groupid) VALUES (%(groupid)s)",
                dict(groupid="GROUP_ID"),
            )
            registrant_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO credentials (registrant_id, org_prefix, username, password, token) VALUES (%(registrant_id)s, %(org_prefix)s, %(username)s, %(password)s, %(token)s)",
                dict(
                    registrant_id=registrant_id,
                    org_prefix="SEECR",
                    username="Bob",
                    password="Secret",
                    token=TOKEN,
                ),
            )
            conn.commit()

    response = environment.client.get(
        "/location/",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 404
    assert response.text == NOT_FOUND

    response = environment.client.get(
        "/location/" + quote("https://some.url", safe=""),
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 404
    assert response.text == NOT_FOUND


async def test_found(environment):
    TOKEN = "THE_SECRET_TOKEN"

    pool = environment.pool
    with pool.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO `registrant` (`registrant_groupid`) VALUES (%(groupid)s)",
                dict(groupid="GROUP_ID"),
            )
            registrant_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO `credentials` (`registrant_id`, `org_prefix`, `username`, `password`, `token`) VALUES (%(registrant_id)s, %(org_prefix)s, %(username)s, %(password)s, %(token)s)",
                dict(
                    registrant_id=registrant_id,
                    org_prefix="SEECR",
                    username="Bob",
                    password="Secret",
                    token=TOKEN,
                ),
            )

            cursor.execute(
                "INSERT INTO `identifier` (`identifier_value`) VALUES (%(identifier_value)s)",
                dict(identifier_value="URN:NBN:"),
            )
            identifier_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO `location` (`location_url`) VALUES (%(location_url)s)",
                dict(location_url="https://seecr.nl"),
            )
            location_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO `identifier_location` (`location_id`, `identifier_id`) VALUES (%(location_id)s, %(identifier_id)s)",
                dict(location_id=location_id, identifier_id=identifier_id),
            )

            conn.commit()

    response = environment.client.get(
        "/location/" + quote("https://seecr.nl", safe=""),
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 200
    assert response.json() == ["URN:NBN:"]
