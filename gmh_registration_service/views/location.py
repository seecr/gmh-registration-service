from starlette.responses import PlainTextResponse, JSONResponse

from gmh_registration_service.messages import INVALID_MESSAGE, NOT_FOUND


def get_user_by_token(pool, token):
    results = []
    with pool.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT org_prefix from credentials where token=%(token)s",
                dict(token=token),
            )
            for hit in cursor:
                results.append(dict(zip(["org_prefix"], hit)))
    return results[0] if len(results) == 1 else None


def get_nbn_by_location(pool, location):
    results = []
    with pool.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT I.identifier_value FROM identifier I JOIN identifier_location IL ON I.identifier_id = IL.identifier_id JOIN location L ON L.location_id = IL.location_id WHERE L.location_url = %(location)s;",
                dict(location=location),
            )
            for hit in cursor:
                results.append(dict(zip(["identifier_value"], hit)))
    return results


async def location(request, pool, **kwargs):
    if (
        authorization := request.headers.get("authorization")
    ) is None or not authorization.startswith("Bearer "):
        return PlainTextResponse(
            INVALID_MESSAGE, status_code=401, headers={"WWW-Authenticate": "Bearer"}
        )

    _, token = authorization.split(" ", 1)
    if get_user_by_token(pool, token) is None:
        return PlainTextResponse(
            INVALID_MESSAGE, status_code=401, headers={"WWW-Authenticate": "Bearer"}
        )

    location = request.path_params.get("location")
    if len(location.strip()) == 0:
        return PlainTextResponse(NOT_FOUND, status_code=404)

    nbns = get_nbn_by_location(pool, location)
    if len(nbns) == 0:
        return PlainTextResponse(NOT_FOUND, status_code=404)

    return JSONResponse([each["identifier_value"] for each in nbns])
