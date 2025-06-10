## begin license ##
#
# Gemeenschappelijke Metadata Harvester (GMH) Registration Service
#  register NBN and urls
#
# Copyright (C) 2025 Koninklijke Bibliotheek (KB) https://www.kb.nl
# Copyright (C) 2025 Seecr (Seek You Too B.V.) https://seecr.nl
#
# This file is part of "GMH-Registration-Service"
#
# "GMH-Registration-Service" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "GMH-Registration-Service" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "GMH-Registration-Service"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from gmh_registration_service.test_utils import (
    environment,
    environment_session,
    insert_token,
    insert_location,
)

from gmh_registration_service.messages import (
    URN_NBN_INVALID,
    URN_NBN_LOCATION_INVALID,
    URN_NBN_FORBIDDEN,
    URN_NBN_FORBIDDEN2,
    URN_NBN_NOT_FOUND,
    URN_NBN_CONFLICT,
    INVALID_AUTH_INFO,
    SUCCESS_CREATED_NEW,
    SUCCESS_UPDATED,
    BAD_REQUEST,
)

from gmh_registration_service.utils import unfragment

from urllib.parse import quote


def _test_auth_for_urls(client, urls, method="get"):
    client_method = dict(get=client.get, post=client.post, put=client.put)[method]

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
    registrant_id = insert_token(
        environment.database, TOKEN, prefix="urn:nbn:nl:ui:42-"
    )
    insert_location(
        environment.database,
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
    registrant_id = insert_token(
        environment.database, TOKEN, prefix="urn:nbn:nl:ui:42-"
    )
    insert_location(
        environment.database,
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
    database = environment.database

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
    insert_token(database, TOKEN, prefix="urn:nbn:nl:ui:42-", isLTP=False)

    # No JSON
    response = environment.client.post(
        "/nbn", headers={"Authorization": f"Bearer {TOKEN}"}, content="W00tW00t"
    )
    assert response.status_code == 400
    assert response.text == BAD_REQUEST

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

    assert database.get_locations(NBN, False) == []
    response = environment.client.post(
        "/nbn",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "identifier": NBN,
            "locations": [URL],
        },
    )
    assert database.get_locations(NBN, False) == [{"uri": URL, "ltp": 0}]

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
    database = environment.database
    TOKEN = "THE_TOKEN"
    NBN = "urn:nbn:nl:ui:42-DEADC0FFEE"
    URL = "https://deadc0ff.ee"

    # Create LTP user
    insert_token(database, TOKEN, prefix="urn:nbn:nl:ui:24-", isLTP=True)

    assert database.get_locations(NBN, True) == []
    response = environment.client.post(
        "/nbn",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "identifier": NBN,
            "locations": [URL],
        },
    )
    assert database.get_locations(NBN, True) == [{"uri": URL, "ltp": 1}]

    assert response.status_code == 201
    assert response.text == SUCCESS_CREATED_NEW


def test_update_nbn_create(environment):
    database = environment.database

    TOKEN = "THE_TOKEN"
    NBN = "urn:nbn:nl:ui:42-DEADC0FFEE#aap"
    URL = "https://deadc0ff.ee"

    # Create NON-LTP user
    insert_token(database, TOKEN, prefix="urn:nbn:nl:ui:42-", isLTP=False)

    _test_auth_for_urls(
        environment.client,
        [
            dict(url=f"/nbn/{NBN}"),
            dict(url=f"/nbn/{NBN}", headers={"Authorization": "Basic 1234"}),
            dict(url=f"/nbn/{NBN}", headers={"Authorization": "Bearer 1234"}),
        ],
        method="put",
    )

    # Invalid URN:NBN
    response = environment.client.put(
        "/nbn/INVALID", headers={"Authorization": f"Bearer {TOKEN}"}, json=[URL]
    )
    assert response.status_code == 400
    assert response.text == URN_NBN_LOCATION_INVALID

    # Invalid location
    response = environment.client.put(
        f"/nbn/{NBN}", headers={"Authorization": f"Bearer {TOKEN}"}, content="INVALID"
    )

    response = environment.client.put(
        f"/nbn/{NBN}", headers={"Authorization": f"Bearer {TOKEN}"}, json=["INVALID"]
    )
    assert response.status_code == 400
    assert response.text == URN_NBN_LOCATION_INVALID

    # Prefix of identifier does not match and current user is not LTP
    response = environment.client.put(
        f"/nbn/urn:nbn:nl:ui:43-DEADC0FFEE",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json=[URL],
    )
    assert response.status_code == 403
    assert response.text == URN_NBN_FORBIDDEN2

    assert database.get_locations(NBN, False) == []
    response = environment.client.put(
        f"/nbn/{NBN}", headers={"Authorization": f"Bearer {TOKEN}"}, json=[URL]
    )
    assert database.get_locations(NBN, False) == [{"uri": unfragment(URL), "ltp": 0}]

    assert response.status_code == 201
    assert response.text == SUCCESS_CREATED_NEW

    # Identifier is already resolvable --> update
    response = environment.client.put(
        f"/nbn/{NBN}",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json=[URL + "/update"],
    )
    assert response.status_code == 200
    assert response.text == SUCCESS_UPDATED
    assert database.get_locations(NBN, False) == [
        {"uri": unfragment(URL) + "/update", "ltp": 0}
    ]


def test_nbn_update_as_LTP(environment):
    database = environment.database
    TOKEN = "THE_TOKEN"
    NBN = "urn:nbn:nl:ui:42-DEADC0FFEE"
    URL = "https://deadc0ff.ee"

    # Create LTP user
    insert_token(database, TOKEN, prefix="urn:nbn:nl:ui:24-", isLTP=True)

    assert database.get_locations(NBN, True) == []
    response = environment.client.put(
        f"/nbn/{NBN}", headers={"Authorization": f"Bearer {TOKEN}"}, json=[URL]
    )
    assert database.get_locations(NBN, True) == [{"uri": URL, "ltp": 1}]

    assert response.status_code == 201
    assert response.text == SUCCESS_CREATED_NEW

    response = environment.client.put(
        f"/nbn/{NBN}",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json=[URL + "/update"],
    )
    assert database.get_locations(NBN, True) == [{"uri": URL + "/update", "ltp": 1}]
    assert response.status_code == 200
    assert response.text == SUCCESS_UPDATED


def test_nbn_update_non_LTP_record_as_LTP(environment):
    database = environment.database
    REGULAR_TOKEN = "REGULAR_TOKEN"
    LTP_TOKEN = "LTP_TOKEN"
    NBN = "urn:nbn:nl:ui:42-DEADC0FFEE"
    URL = "https://deadc0ff.ee"

    # Create LTP user
    insert_token(database, REGULAR_TOKEN, prefix="urn:nbn:nl:ui:42-", isLTP=False)
    insert_token(
        database,
        LTP_TOKEN,
        groupid="ltp",
        username="ltp",
        prefix="urn:nbn:nl:ui:24-",
        isLTP=True,
    )

    assert database.get_locations(NBN, True) == []
    response = environment.client.put(
        f"/nbn/{NBN}", headers={"Authorization": f"Bearer {REGULAR_TOKEN}"}, json=[URL]
    )
    assert database.get_locations(NBN, True) == [{"uri": URL, "ltp": 0}]

    assert response.status_code == 201
    assert response.text == SUCCESS_CREATED_NEW

    response = environment.client.put(
        f"/nbn/{NBN}",
        headers={"Authorization": f"Bearer {LTP_TOKEN}"},
        json=[URL + "/update"],
    )
    assert database.get_locations(NBN, True) == [
        {"uri": URL, "ltp": 0},
        {"uri": URL + "/update", "ltp": 1},
    ]
    assert response.status_code == 200
    assert response.text == SUCCESS_UPDATED
