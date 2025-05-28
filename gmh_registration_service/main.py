import argparse
import asyncio
import pathlib

from swl import configure_logging, uvicorn_main

from gmh_registration_service.config import Config
from gmh_registration_service.server import create_app


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
