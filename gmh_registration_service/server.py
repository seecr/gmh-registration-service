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

import jinja2
import swl
import logging

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

from .database import Database

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

    database = Database(**config.database_config)

    templates.env.globals["register"] = actions.register
    templates.env.globals["VERSION"] = VERSION
    templates.env.globals["app_title"] = "NBN Resolver Swagger API"
    templates.env.globals["SWL"] = swl.SWL(
        resources_path=global_config_path / "web-resources.json",
    )

    settings = {"development": config.development}
    actions.register_kwarg("settings", settings)
    actions.register_kwarg("templates", templates)
    actions.register_kwarg("database", database)

    return actions, templates, database


async def create_app(config, environment=None, **_):
    (actions, templates, _) = environment or await setup_environment(config=config)

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
                "/nbn/{identifier:str}",
                endpoint=aw(VIEWS.nbn.nbn_update),
                methods=["PUT"],
            ),
            Route(
                "/nbn/{identifier:str}/locations",
                endpoint=aw(VIEWS.nbn.nbn_get_locations),
                methods=["GET"],
            ),
        ],
        middleware=[],
    )
