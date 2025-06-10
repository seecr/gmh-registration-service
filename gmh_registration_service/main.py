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

import argparse
import asyncio
import pathlib
import getpass

from swl import configure_logging, uvicorn_main

from gmh_registration_service.config import Config
from gmh_registration_service.server import create_app
from gmh_registration_service.database import Database


def passwd():
    parser = argparse.ArgumentParser(
        prog="GMH Registration Service - passwd", description="Password management"
    )
    parser.add_argument(
        "--data-path",
        required=True,
        type=pathlib.Path,
        help="Path to data directory which will contain config directory and store data",
    )

    parser.add_argument(
        "--username",
        required=True,
        type=str,
        help="Username to set password for",
    )
    parser.add_argument(
        "--groupid",
        required=True,
        type=str,
        help="Groupid of registrant",
    )

    args = parser.parse_args()
    config = Config(args.data_path, False)

    database = Database(**config.database_config)
    new_password = getpass.getpass("New password: ")
    database.set_password(args.groupid, args.username, new_password)


def main_app():
    parser = argparse.ArgumentParser(
        prog="GMH Registration Service", description="Swagger API for GMH"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to, default %(default)s",
    )
    parser.add_argument(
        "--port", type=int, default="9000", help="Port to bind to, default %(default)s"
    )
    parser.add_argument(
        "--data-path",
        required=True,
        type=pathlib.Path,
        help="Path to data directory which will contain config directory and store data",
    )
    parser.add_argument(
        "--development",
        action="store_true",
        help="Run in development mode.",
        default=False,
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Log level, default %(default)s",
    )
    args = parser.parse_args()

    configure_logging(args.log_level)

    arg_vars = vars(args)

    config = Config(args.data_path, development=arg_vars.pop("development", False))

    asyncio.run(
        uvicorn_main(
            create_app=create_app,
            config=config,
            deproxy_ips=config.deproxy_ips,
            **arg_vars,
        )
    )
