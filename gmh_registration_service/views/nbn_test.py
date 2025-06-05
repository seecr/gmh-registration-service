from gmh_registration_service.test_utils import (
    environment,
    environment_session,
    insert_token,
    insert_location,
)
from gmh_registration_service.messages import (
    URN_NBN_INVALID,
    URN_NBN_FORBIDDEN,
    URN_NBN_NOT_FOUND,
    INVALID_AUTH_INFO,
)

from urllib.parse import quote


def _test_auth_for_urls(client, urls):
    for url in urls:
        response = client.get(**url)
        assert response.status_code == 401
        assert response.text == INVALID_AUTH_INFO
        assert "WWW-Authenticate" in response.headers
        assert response.headers.get("WWW-Authenticate") == "Bearer"


async def test_get_nbn_auth(environment):
    _test_auth_for_urls(
        environment.client,
        [
            dict(url="/nbn/identifier"),
            dict(url="/nbn/identifier", headers={"Authorization": "Basic 1234"}),
            dict(url="/nbn/identifier", headers={"Authorization": "Bearer 1234"}),
        ],
    )


async def test_get_nbn(environment):
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


async def test_get_nbn_locations_auth(environment):
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


async def test_get_nbn_locations(environment):
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
