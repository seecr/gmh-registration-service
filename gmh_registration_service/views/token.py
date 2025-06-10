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

from starlette.responses import PlainTextResponse
from starlette.exceptions import HTTPException

import secrets
import base64

from gmh_registration_service.messages import (
    INTERNAL_ERROR,
    INVALID_CREDENTIALS,
)
from gmh_registration_service.utils import parse_body_as_json

import logging

logger = logging.getLogger(__name__)


def random_token(size=48):
    return base64.b64encode(secrets.token_bytes(size))


async def token(request, database, **kwargs):
    user_credentials = await parse_body_as_json(request)

    username = user_credentials.get("username")
    password = user_credentials.get("password")

    try:
        new_token = _new_token(database, username, password)
    except HTTPException:
        raise
    except Exception:
        logging.exception("token")
        raise HTTPException(status_code=500, detail=INTERNAL_ERROR)

    return PlainTextResponse(content=new_token, status_code=200)


def _new_token(database, username, password):
    if (
        credentials_id := database.validate_user_credentials(username, password)
    ) is None:
        raise HTTPException(status_code=403, detail=INVALID_CREDENTIALS)

    new_token = random_token()
    database.update_token(new_token, credentials_id)

    return new_token
