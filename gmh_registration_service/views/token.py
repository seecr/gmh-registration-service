from starlette.responses import PlainTextResponse

import secrets
import base64

from gmh_registration_service.messages import INVALID_MESSAGE, INTERNAL_ERROR
from gmh_registration_service.utils import select_query


def random_token(size=48):
    return base64.b64encode(secrets.token_bytes(size))


async def token(request, pool, **kwargs):
    async with request.form() as form:
        username = form.get("username")
        password = form.get("password")

        try:
            new_token = _new_token(pool, username, password)
        except:
            return PlainTextResponse(
                content=INTERNAL_ERROR,
                status_code=500,
            )

        if new_token is None:
            return PlainTextResponse(
                content=INVALID_MESSAGE,
                status_code=401,
            )

        return PlainTextResponse(content=new_token, status_code=200)


def _new_token(pool, username, password):
    if username is None or password is None:
        return None

    results = select_query(
        pool,
        ["org_prefix"],
        "credentials",
        "`username` = %(username)s AND `password` = %(password)s;",
        dict(username=username, password=password),
    )

    if len(results) == 0:
        return None

    new_token = random_token()
    with pool.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE `credentials` SET `token`=%(token)s WHERE `username` = %(username)s AND `password` = %(password)s;",
                dict(token=new_token, username=username, password=password),
            )
            conn.commit()

    return new_token
