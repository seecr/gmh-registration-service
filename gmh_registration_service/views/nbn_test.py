from gmh_registration_service.test_utils import (
    environment,
    environment_session,
    insert_token,
    insert_location,
)

from gmh_registration_service.database import get_locations

from gmh_registration_service.messages import (
    URN_NBN_INVALID,
    URN_NBN_LOCATION_INVALID,
    URN_NBN_FORBIDDEN,
    URN_NBN_FORBIDDEN2,
    URN_NBN_NOT_FOUND,
    URN_NBN_CONFLICT,
    INVALID_AUTH_INFO,
    SUCCESS_CREATED_NEW,
)

from urllib.parse import quote


def _test_auth_for_urls(client, urls, method="get"):
    client_method = client.get if method == "get" else client.post
    for url in urls:
        response = client_method(**url)
        assert response.status_code == 401
        assert response.text == INVALID_AUTH_INFO
        assert "WWW-Authenticate" in response.headers
        assert response.headers.get("WWW-Authenticate") == "Bearer"


async def test_get_nbn(environment):
    _test_auth_for_urls(
        environment.client,
        [
            dict(url="/nbn/identifier"),
            dict(url="/nbn/identifier", headers={"Authorization": "Basic 1234"}),
            dict(url="/nbn/identifier", headers={"Authorization": "Bearer 1234"}),
        ],
    )

    TOKEN = "THE_TOKEN"
    REQUESTED_NBN = "urn:nbn:nl:ui:42-DEADC0FFEE"
    registrant_id = insert_token(environment.pool, TOKEN, prefix="urn:nbn:nl:ui:42-")
    insert_location(
        environment.pool,
        identifier=REQUESTED_NBN,
        location="https://deadcoff.ee",
        registrant=registrant_id,
    )

    # Invalid NBN
    response = environment.client.get(
        f"/nbn/invalid",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 400
    assert response.text == URN_NBN_INVALID

    response = environment.client.get(
        f"/nbn/urn:nbn:XX:ui:42-DEADC0FFEE",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 400
    assert response.text == URN_NBN_INVALID

    # Forbidden (Prefix of NBN does not match registrant prefix)
    response = environment.client.get(
        f"/nbn/urn:nbn:nl:ui:43-DEADC0FFEE",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 403
    assert response.text == URN_NBN_FORBIDDEN

    # Not Found
    response = environment.client.get(
        f"/nbn/urn:nbn:nl:ui:42-CAFEBABE",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 404
    assert response.text == URN_NBN_NOT_FOUND

    response = environment.client.get(
        f"/nbn/{REQUESTED_NBN}",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "identifier": REQUESTED_NBN,
        "locations": ["https://deadcoff.ee"],
    }


async def test_get_nbn_locations(environment):
    _test_auth_for_urls(
        environment.client,
        [
            dict(url="/nbn/identifier/locations"),
            dict(
                url="/nbn/identifier/locations", headers={"Authorization": "Basic 1234"}
            ),
            dict(
                url="/nbn/identifier/locations",
                headers={"Authorization": "Bearer 1234"},
            ),
        ],
    )

    TOKEN = "THE_TOKEN"
    REQUESTED_NBN = "urn:nbn:nl:ui:42-DEADC0FFEE"
    registrant_id = insert_token(environment.pool, TOKEN, prefix="urn:nbn:nl:ui:42-")
    insert_location(
        environment.pool,
        identifier=REQUESTED_NBN,
        location="https://deadcoff.ee",
        registrant=registrant_id,
    )

    # Invalid NBN
    response = environment.client.get(
        f"/nbn/invalid/locations",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 400
    assert response.text == URN_NBN_INVALID

    response = environment.client.get(
        f"/nbn/urn:nbn:XX:ui:42-DEADC0FFEE/locations",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 400
    assert response.text == URN_NBN_INVALID

    # Forbidden (Prefix of NBN does not match registrant prefix)
    response = environment.client.get(
        f"/nbn/urn:nbn:nl:ui:43-DEADC0FFEE/locations",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 403
    assert response.text == URN_NBN_FORBIDDEN

    # Not Found
    response = environment.client.get(
        f"/nbn/urn:nbn:nl:ui:42-CAFEBABE/locations",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 404
    assert response.text == URN_NBN_NOT_FOUND

    response = environment.client.get(
        f"/nbn/{REQUESTED_NBN}/locations",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )

    assert response.status_code == 200
    assert response.json() == ["https://deadcoff.ee"]


def test_nbn(environment):
    pool = environment.pool

    _test_auth_for_urls(
        environment.client,
        [
            dict(url="/nbn"),
            dict(url="/nbn", headers={"Authorization": "Basic 1234"}),
            dict(url="/nbn", headers={"Authorization": "Bearer 1234"}),
        ],
        method="post",
    )

    TOKEN = "THE_TOKEN"
    NBN = "urn:nbn:nl:ui:42-DEADC0FFEE"
    URL = "https://deadc0ff.ee"

    # Create NON-LTP user
    insert_token(pool, TOKEN, prefix="urn:nbn:nl:ui:42-", isLTP=False)

    # Invalid URN:NBN
    response = environment.client.post(
        "/nbn",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "identifier": "INVALID",
            "locations": [URL],
        },
    )
    assert response.status_code == 400
    assert response.text == URN_NBN_LOCATION_INVALID

    # Invalid location
    response = environment.client.post(
        "/nbn",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "identifier": NBN,
            "locations": ["INVALID"],
        },
    )
    assert response.status_code == 400
    assert response.text == URN_NBN_LOCATION_INVALID

    # Prefix of identifier does not match and current user is not LTP
    response = environment.client.post(
        "/nbn",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "identifier": "urn:nbn:nl:ui:43-DEADC0FFEE",
            "locations": [URL],
        },
    )
    assert response.status_code == 403
    assert response.text == URN_NBN_FORBIDDEN2

    assert get_locations(pool, NBN, False) == []
    response = environment.client.post(
        "/nbn",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "identifier": NBN,
            "locations": [URL],
        },
    )
    assert get_locations(pool, NBN, False) == [{"uri": URL, "ltp": 0}]

    assert response.status_code == 201
    assert response.text == SUCCESS_CREATED_NEW

    # Identifier is already resolvable
    response = environment.client.post(
        "/nbn",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "identifier": NBN,
            "locations": [URL],
        },
    )
    assert response.status_code == 409
    assert response.text == URN_NBN_CONFLICT


def test_nbn_as_LTP(environment):
    pool = environment.pool
    TOKEN = "THE_TOKEN"
    NBN = "urn:nbn:nl:ui:42-DEADC0FFEE"
    URL = "https://deadc0ff.ee"

    # Create NON-LTP user
    insert_token(pool, TOKEN, prefix="urn:nbn:nl:ui:24-", isLTP=True)

    assert get_locations(pool, NBN, True) == []
    response = environment.client.post(
        "/nbn",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "identifier": NBN,
            "locations": [URL],
        },
    )
    assert get_locations(pool, NBN, True) == [{"uri": URL, "ltp": 1}]

    assert response.status_code == 201
    assert response.text == SUCCESS_CREATED_NEW
