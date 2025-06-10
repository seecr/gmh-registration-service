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
from gmh_registration_service.messages import INVALID_AUTH_INFO, NOT_FOUND

from urllib.parse import quote


async def test_auth(environment):
    response = environment.client.get("/location/some_location")
    assert response.status_code == 401
    assert response.text == INVALID_AUTH_INFO
    assert "WWW-Authenticate" in response.headers
    assert response.headers.get("WWW-Authenticate") == "Bearer"

    response = environment.client.get(
        "/location/some_location", headers={"Authorization": "Basic 1234"}
    )
    assert response.status_code == 401
    assert response.text == INVALID_AUTH_INFO
    assert "WWW-Authenticate" in response.headers
    assert response.headers.get("WWW-Authenticate") == "Bearer"

    response = environment.client.get(
        "/location/some_location", headers={"Authorization": "Bearer SOME_TOKEN"}
    )
    assert response.status_code == 401
    assert response.text == INVALID_AUTH_INFO
    assert "WWW-Authenticate" in response.headers
    assert response.headers.get("WWW-Authenticate") == "Bearer"


async def test_not_found(environment):
    TOKEN = "THE_SECRET_TOKEN"
    insert_token(environment.database, TOKEN)

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
    registrant_id = insert_token(environment.database, TOKEN)
    insert_location(
        environment.database,
        identifier="URN:NBN:",
        location="https://seecr.nl",
        registrant=registrant_id,
    )

    response = environment.client.get(
        "/location/" + quote("https://seecr.nl", safe=""),
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    assert response.status_code == 200
    assert response.json() == ["URN:NBN:"]
