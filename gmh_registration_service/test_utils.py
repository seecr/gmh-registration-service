import pytest

from ._path import global_config_path
from gmh_registration_service.config import Config
from gmh_registration_service.server import create_app, setup_environment
from starlette.testclient import TestClient
from collections import namedtuple
from contextlib import asynccontextmanager

import bcrypt


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
    pool = environment_session.pool
    with pool.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            for table_name in [
                "registrant",
                "credentials",
                "location",
                "identifier",
                "identifier_location",
                "identifier_registrant",
            ]:
                cursor.execute(f"TRUNCATE TABLE {table_name}")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1; ")

    yield environment_session


Environment = namedtuple(
    "Environment",
    ["client", "actions", "templates", "pool"],
)


def insert_token(
    pool,
    token,
    groupid="GROUP_ID",
    username="bob",
    password="Secret",
    prefix="urn:nbn:nl:",
    isLTP=False,
):

    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    with pool.get_connection() as conn:
        with conn.cursor() as cursor:
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
            conn.commit()

            return registrant_id


def insert_location(pool, identifier, location, registrant):
    with pool.get_connection() as conn:
        with conn.cursor() as cursor:
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

            conn.commit()
