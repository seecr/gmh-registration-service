import jinja2
import swl
import logging

from mysql.connector.pooling import MySQLConnectionPool

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from . import VERSION
from ._path import global_config_path, static_path, templates_path
from .views import VIEWS

logger = logging.getLogger(__name__)


async def setup_environment(config):
    actions = swl.Actions()
    actions.register_module(*VIEWS.modules)

    template_paths = [templates_path, swl.templates_dir]

    templates = Jinja2Templates(
        env=jinja2.Environment(
            undefined=jinja2.StrictUndefined,
            loader=jinja2.FileSystemLoader(template_paths),
            autoescape=True,
        )
    )

    pool = MySQLConnectionPool(
        pool_reset_session=True, pool_size=5, **config.database_config
    )

    templates.env.globals["register"] = actions.register
    templates.env.globals["VERSION"] = VERSION
    templates.env.globals["app_title"] = "NBN Resolver Swagger API"
    templates.env.globals["SWL"] = swl.SWL(
        resources_path=global_config_path / "web-resources.json",
    )

    settings = {"development": config.development}
    actions.register_kwarg("settings", settings)
    actions.register_kwarg("templates", templates)
    actions.register_kwarg("pool", pool)

    return actions, templates, pool


async def create_app(config, environment=None, **_):
    (actions, templates, pool) = environment or await setup_environment(config=config)

    # @contextlib.asynccontextmanager
    # async def lifespan(app):
    #    await store.connect()
    #    yield
    #    await store.disconnect()

    aw = actions.wrap

    return Starlette(
        debug=True,
        routes=[
            Mount(
                "/static",
                StaticFiles(
                    directory=static_path.as_posix(),
                    packages=[("swl", "static")],
                ),
                name="static",
            ),
            Route(
                "/action/{action:str}", endpoint=actions.handle, methods=["GET", "POST"]
            ),
            Route("/", endpoint=aw(VIEWS.general.main)),
            Route(
                "/api/v1/openapi.yaml",
                endpoint=aw(VIEWS.openapi.openapi),
                methods=["GET"],
            ),
            Route("/token", endpoint=aw(VIEWS.token.token), methods=["POST"]),
            Route(
                "/location/{location:path}",
                endpoint=aw(VIEWS.location.location),
                methods=["GET"],
            ),
            Route(
                "/nbn",
                endpoint=aw(VIEWS.nbn.nbn),
                methods=["POST"],
            ),
            Route(
                "/nbn/{identifier:str}",
                endpoint=aw(VIEWS.nbn.nbn_get),
                methods=["GET"],
            ),
            Route(
                "/nbn/{identifier:str}/locations",
                endpoint=aw(VIEWS.nbn.nbn_get_locations),
                methods=["GET"],
            ),
        ],
        middleware=[
            # Middleware(SessionMiddleware, secret_key=config.session_secret_key),
        ],
        # lifespan=lifespan,
    )
