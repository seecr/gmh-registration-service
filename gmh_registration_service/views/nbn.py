from starlette.responses import PlainTextResponse, JSONResponse

from gmh_registration_service.messages import (
    INVALID_AUTH_INFO,
    URN_NBN_FORBIDDEN,
    URN_NBN_INVALID,
    URN_NBN_NOT_FOUND,
)

from gmh_registration_service.utils import (
    valid_urn_nbn,
    get_user_by_token,
    has_ltp_location,
    get_locations,
)


INVALID_AUTH_RESPONSE = PlainTextResponse(
    INVALID_AUTH_INFO, status_code=401, headers={"WWW-Authenticate": "Bearer"}
)


async def _nbn_get_locations_by_identifier(request, pool, urn_nbn, format_answer):
    if (
        authorization := request.headers.get("authorization")
    ) is None or not authorization.startswith("Bearer "):
        return INVALID_AUTH_RESPONSE

    _, token = authorization.split(" ", 1)
    if (user := get_user_by_token(pool, token)) is None:
        return INVALID_AUTH_RESPONSE

    if not valid_urn_nbn(urn_nbn):
        return PlainTextResponse(URN_NBN_INVALID, status_code=400)

    if not urn_nbn.lower().startswith(user["prefix"].lower()) and not has_ltp_location(
        pool, identifier=urn_nbn, org_prefix=user["prefix"]
    ):
        return PlainTextResponse(URN_NBN_FORBIDDEN, status_code=403)

    if len(locations := get_locations(pool, identifier=urn_nbn, include_ltp=True)) == 0:
        return PlainTextResponse(URN_NBN_NOT_FOUND, status_code=404)

    return JSONResponse(format_answer(urn_nbn, locations))


async def nbn_get(request, pool, **kwargs):
    def format_answer(identifier, locations):
        return {
            "identifier": identifier,
            "locations": [location["uri"] for location in locations],
        }

    return await _nbn_get_locations_by_identifier(
        request, pool, request.path_params.get("identifier"), format_answer
    )


async def nbn_get_locations(request, pool, **kwargs):
    def format_answer(identifier, locations):
        return [location["uri"] for location in locations]

    return await _nbn_get_locations_by_identifier(
        request, pool, request.path_params.get("identifier"), format_answer
    )
