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

import re

from .messages import INVALID_AUTH_INFO, BAD_REQUEST

from starlette.exceptions import HTTPException


urnnbn_regex = re.compile(
    "^[uU][rR][nN]:[nN][bB][nN]:[nN][lL](:([a-zA-Z]{2}))?:\\d{2}-.+"
)

location_regex = re.compile(
    "https?:\\/\\/(www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b([-a-zA-Z0-9()@:%_\\+.~#?&//=]*)"
)


def valid_urn_nbn(identifier):
    return urnnbn_regex.match(identifier) is not None


def valid_location(location):
    return location_regex.match(location) is not None


def unfragment(identifier):
    return identifier.split("#", 1)[0]


def get_user_by_token(request, database):
    if (
        authorization := request.headers.get("authorization")
    ) is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail=INVALID_AUTH_INFO,
            headers={"WWW-Authenticate": "Bearer"},
        )

    _, token = authorization.split(" ", 1)
    if (user := database.get_user_by_token(token)) is None:
        raise HTTPException(
            status_code=401,
            detail=INVALID_AUTH_INFO,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def parse_body_as_json(request):
    if request.headers.get("content-type") != "application/json":
        raise HTTPException(status_code=400, detail=BAD_REQUEST)

    try:
        body = await request.json()
    except:
        raise HTTPException(status_code=400, detail=BAD_REQUEST)
    return body
