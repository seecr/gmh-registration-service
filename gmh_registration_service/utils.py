import re

from .database import get_user_by_token as _get_user_by_token
from .messages import INVALID_AUTH_INFO

from starlette.exceptions import HTTPException


urnnbn_regex = re.compile(
    "^[uU][rR][nN]:[nN][bB][nN]:[nN][lL](:([a-zA-Z]{2}))?:\\d{2}-.+"
)

location_regex = re.compile(
    "https?:\\/\\/(www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b([-a-zA-Z0-9()@:%_\\+.~#?&//=]*)"
)


def valid_urn_nbn(identifier):
    return urnnbn_regex.match(identifier) is not None


def valid_location(location):
    return location_regex.match(location) is not None


def get_user_by_token(request, pool):
    if (
        authorization := request.headers.get("authorization")
    ) is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail=INVALID_AUTH_INFO,
            headers={"WWW-Authenticate": "Bearer"},
        )

    _, token = authorization.split(" ", 1)
    if (user := _get_user_by_token(pool, token)) is None:
        raise HTTPException(
            status_code=401,
            detail=INVALID_AUTH_INFO,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
