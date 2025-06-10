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

FROM python:3.11-slim

LABEL maintainer="Thijs Janssen <thijs@seecr.nl>"

RUN useradd -m -u 1000 -s /bin/bash seecr

RUN mkdir /src /data && \
    chown seecr:seecr /src /data

RUN cat > /etc/pip.conf <<EOF
[global]
index-url = https://devpi.vpn.seecr.nl/seecr/dev/+simple/
EOF

RUN python3 -m pip install --upgrade pip

# optimization: install dependencies first, so that we can cache them
RUN python3 -m pip install aiohttp asyncio Jinja2 \
                           packaging pytest pytest-asyncio starlette \
                           swl

COPY pyproject.toml /src/
COPY gmh_registration_service /src/gmh_registration_service

WORKDIR /src

ARG PSEUDO_VERSION
RUN test -n "${PSEUDO_VERSION}"
RUN SETUPTOOLS_SCM_PRETEND_VERSION=${PSEUDO_VERSION} python3 -m pip install --editable .

USER seecr

VOLUME /data

EXPOSE 8000

ENTRYPOINT ["gmh-registration-service-server", "--data-path", "/data", "--port", "8000"]
CMD []
