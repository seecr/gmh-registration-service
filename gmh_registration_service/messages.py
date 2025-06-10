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

INVALID_AUTH_INFO = "Authentication information is missing or invalid"
INVALID_CREDENTIALS = "Invalid credentials"

URN_NBN_FORBIDDEN = "URN:NBN-prefix is not registered to this user"
URN_NBN_FORBIDDEN2 = "URN:NBN identifier is valid, but does not match the prefix of the authenticated user"
URN_NBN_NOT_FOUND = "Supplied URN:NBN identifier not found"
URN_NBN_INVALID = "Invalid URN:NBN identifier pattern supplied"
URN_NBN_LOCATION_INVALID = (
    "Invalid URN:NBN identifier pattern or location uri(s) supplied"
)
URN_NBN_CONFLICT = "Conflict, resource already exists"

SUCCESS_CREATED_NEW = "Successful operation (created new)"
SUCCESS_UPDATED = "OK (updated existing)"

BAD_REQUEST = "Bad request"
INTERNAL_ERROR = "Internal server error"
NOT_FOUND = "Object (location) not found"
