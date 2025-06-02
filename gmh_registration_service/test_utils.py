import pytest

from ._path import global_config_path
from gmh_registration_service.config import Config
from gmh_registration_service.server import create_app, setup_environment
from starlette.testclient import TestClient
from collections import namedtuple
from contextlib import asynccontextmanager


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
            for table_name in ["registrant", "credentials"]:
                cursor.execute(f"TRUNCATE TABLE {table_name}")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1; ")

    yield environment_session


Environment = namedtuple(
    "Environment",
    ["client", "actions", "templates", "pool"],
)
