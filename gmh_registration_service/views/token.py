from starlette.responses import PlainTextResponse

import secrets
import base64

INVALID_MESSAGE = "Authentication information is missing or invalid"
INTERNAL_ERROR = "Internal server error"


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

    results = []
    with pool.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT `org_prefix` FROM `credentials` WHERE `username` = %(username)s AND `password` = %(password)s;",
                dict(username=username, password=password),
            )
            for hit in cursor:
                results.append(dict(zip(["org_prefix"], hit)))

    if len(results) == 0:
        return None

    new_token = random_token()
    with pool.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE `credentials` SET `token`=%(token)s WHERE `username` = %(username)s AND `password` = %(password)s;",
                dict(token=new_token, username=username, password=password),
            )

    return new_token
