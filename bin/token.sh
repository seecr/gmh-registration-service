#!/bin/bash
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

#

if [ -z "${RESOLVER_URL}" ]; then
    echo "Please set RESOLVER_URL to something like https://resolver-ui.acc.kb.seecr.nl/gmh-registration-service"
    exit 1
fi

read -s -p "Password: " PASSWD

TOKEN=$(wget --quiet \
    -O- "${RESOLVER_URL}/token" \
    --post-data='{"username": "seecr", "password": "'${PASSWD}'"}' \
    --header 'Content-type: application/json')

echo "TOKEN: ${TOKEN}"

