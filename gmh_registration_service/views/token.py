from starlette.responses import PlainTextResponse

import secrets
import base64
import bcrypt

from gmh_registration_service.messages import (
    INTERNAL_ERROR,
    INVALID_CREDENTIALS,
    BAD_REQUEST,
)
from gmh_registration_service.utils import select_query

import logging

logger = logging.getLogger(__name__)


def random_token(size=48):
    return base64.b64encode(secrets.token_bytes(size))


async def token(request, pool, **kwargs):
    if request.headers.get("content-type") != "application/json":
        return PlainTextResponse(
            content=BAD_REQUEST,
            status_code=400,
        )

    user_credentials = await request.json()
    username = user_credentials.get("username")
    password = user_credentials.get("password")

    try:
        new_token = _new_token(pool, username, password)
    except Exception:
        logging.exception("token")

        return PlainTextResponse(
            content=INTERNAL_ERROR,
            status_code=500,
        )

    if new_token is None:
        return PlainTextResponse(
            content=INVALID_CREDENTIALS,
            status_code=403,
        )

    return PlainTextResponse(content=new_token, status_code=200)


def _new_token(pool, username, password):
    if username is None or password is None:
        return None

    results = select_query(
        pool,
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
    with pool.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE `credentials` SET `token`=%(token)s WHERE `credentials_id` = %(credentials_id)s",
                dict(token=new_token, credentials_id=results[0]["credentials_id"]),
            )
            conn.commit()

    return new_token
