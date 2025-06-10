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
