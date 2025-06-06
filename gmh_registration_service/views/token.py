from starlette.responses import PlainTextResponse
from starlette.exceptions import HTTPException

import secrets
import base64
import bcrypt

from gmh_registration_service.messages import (
    INTERNAL_ERROR,
    INVALID_CREDENTIALS,
    BAD_REQUEST,
)
from gmh_registration_service.utils import parse_body_as_json

import logging

logger = logging.getLogger(__name__)


def random_token(size=48):
    return base64.b64encode(secrets.token_bytes(size))


async def token(request, database, **kwargs):
    user_credentials = await parse_body_as_json(request)

    username = user_credentials.get("username")
    password = user_credentials.get("password")

    try:
        new_token = _new_token(database, username, password)
    except Exception:
        logging.exception("token")
        raise HTTPException(status_code=500, detail=INTERNAL_ERROR)

    if new_token is None:
        raise HTTPException(status_code=403, detail=INVALID_CREDENTIALS)

    return PlainTextResponse(content=new_token, status_code=200)


def _new_token(database, username, password):
    if username is None or password is None:
        return None

    results = database.select_query(
        ["credentials_id", "password"],
        "credentials",
        "`username` = %(username)s;",
        dict(username=username),
    )

    if (
        len(results) == 0
        or bcrypt.checkpw(
            password.encode("utf-8"), results[0]["password"].encode("utf-8")
        )
        is False
    ):
        return None

    new_token = random_token()
    with database.cursor() as cursor:
        cursor.execute(
            "UPDATE `credentials` SET `token`=%(token)s WHERE `credentials_id` = %(credentials_id)s",
            dict(token=new_token, credentials_id=results[0]["credentials_id"]),
        )

    return new_token
