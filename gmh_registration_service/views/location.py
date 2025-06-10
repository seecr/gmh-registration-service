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

from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException

from gmh_registration_service.messages import NOT_FOUND
from gmh_registration_service.utils import get_user_by_token


async def location(request, database, **kwargs):
    # Raises HTTPException if no authorization or valid user
    get_user_by_token(request, database)

    location = request.path_params.get("location")
    if len(location.strip()) == 0:
        raise HTTPException(status_code=404, detail=NOT_FOUND)

    if len(nbns := database.get_nbn_by_location(location)) == 0:
        raise HTTPException(status_code=404, detail=NOT_FOUND)
    return JSONResponse([each["identifier_value"] for each in nbns])
