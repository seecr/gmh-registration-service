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

import pytest

from ._path import global_config_path
from gmh_registration_service.config import Config
from gmh_registration_service.server import create_app, setup_environment
from starlette.testclient import TestClient
from collections import namedtuple
from contextlib import asynccontextmanager

import bcrypt

Environment = namedtuple(
    "Environment",
    ["client", "actions", "templates", "database"],
)


@pytest.fixture(scope="session")
async def environment_session(tmp_path_factory):
    data_path = tmp_path_factory.mktemp("data")
    config_path = data_path / "config"
    config_path.mkdir(parents=True)
    import shutil

    if not (global_config_path / "database.config").is_file():
        raise RuntimeError(f"database.config not found in {global_config_path}")
    shutil.copy(global_config_path / "database.config", config_path / "database.conf")

    config = Config(data_path, development=True)
    env = await setup_environment(config)
    client = TestClient((await create_app(config=config, environment=env)))

    return Environment(client, *env)


@asynccontextmanager
@pytest.fixture
async def environment(environment_session):
    database = environment_session.database
    all_tables = [
        "registrant",
        "credentials",
        "location",
        "identifier",
        "identifier_location",
        "identifier_registrant",
    ]

    database.execute_statements(
        ["SET FOREIGN_KEY_CHECKS = 0"]
        + [f"TRUNCATE TABLE {table_name}" for table_name in all_tables]
        + ["SET FOREIGN_KEY_CHECKS = 1"]
    )
    yield environment_session


def insert_token(
    database,
    token,
    groupid="GROUP_ID",
    username="bob",
    password="Secret",
    prefix="urn:nbn:nl:",
    isLTP=False,
):

    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    with database.cursor() as cursor:
        cursor.execute(
            "INSERT INTO registrant (registrant_groupid, prefix, isLTP) VALUES (%(groupid)s, %(prefix)s, %(isLTP)s)",
            dict(groupid=groupid, prefix=prefix, isLTP=isLTP),
        )
        registrant_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO credentials (registrant_id, username, password, token) VALUES (%(registrant_id)s, %(username)s, %(password)s, %(token)s)",
            dict(
                registrant_id=registrant_id,
                username=username,
                password=hashed_password,
                token=token,
            ),
        )

        return registrant_id


def insert_location(database, identifier, location, registrant):
    with database.cursor() as cursor:
        cursor.execute(
            "INSERT INTO `identifier` (`identifier_value`) VALUES (%(identifier_value)s)",
            dict(identifier_value=identifier),
        )
        identifier_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO `location` (`location_url`) VALUES (%(location_url)s)",
            dict(location_url=location),
        )
        location_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO `identifier_location` (`location_id`, `identifier_id`) VALUES (%(location_id)s, %(identifier_id)s)",
            dict(location_id=location_id, identifier_id=identifier_id),
        )

        cursor.execute(
            "INSERT INTO `identifier_registrant` (`registrant_id`, `identifier_id`) VALUES (%(registrant_id)s, %(identifier_id)s)",
            dict(registrant_id=registrant, identifier_id=identifier_id),
        )
