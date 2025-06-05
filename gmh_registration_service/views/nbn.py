from starlette.responses import PlainTextResponse, JSONResponse
from starlette.exceptions import HTTPException

from gmh_registration_service.messages import (
    INVALID_AUTH_INFO,
    URN_NBN_FORBIDDEN,
    URN_NBN_INVALID,
    URN_NBN_NOT_FOUND,
    SUCCESS_CREATED_NEW,
)

from gmh_registration_service.utils import (
    valid_urn_nbn,
    get_user_by_token,
    has_ltp_location,
    get_locations,
)


def _get_user_by_token(request, pool):
    if (
        authorization := request.headers.get("authorization")
    ) is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail=INVALID_AUTH_INFO,
            headers={"WWW-Authenticate": "Bearer"},
        )

    _, token = authorization.split(" ", 1)
    if (user := get_user_by_token(pool, token)) is None:
        raise HTTPException(
            status_code=401,
            detail=INVALID_AUTH_INFO,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def _nbn_get_locations_by_identifier(request, pool, urn_nbn, format_answer):
    user = _get_user_by_token(request, pool)

    if not valid_urn_nbn(urn_nbn):
        raise HTTPException(status_code=400, detail=URN_NBN_INVALID)

    if not urn_nbn.lower().startswith(user["prefix"].lower()) and not has_ltp_location(
        pool, identifier=urn_nbn, org_prefix=user["prefix"]
    ):
        raise HTTPException(status_code=403, detail=URN_NBN_FORBIDDEN)

    if len(locations := get_locations(pool, identifier=urn_nbn, include_ltp=True)) == 0:
        raise HTTPException(status_code=404, detail=URN_NBN_NOT_FOUND)

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


async def nbn(request, pool, **kwargs):
    user = _get_user_by_token(request, pool)

    body = await request.json()
    identifier = body.get("identifier")
    locations = body.get("locations")

    # validate identifier
    # validate locations
    # bad request if identifier/locations not valid

    # prefix match registrant prefix with identifier
    # forbidden is no match

    # determine if identifier is resolvable (already has locations associated)

    await add_nbn_locations(identifier, locations, user)

    return PlainTextResponse(SUCCESS_CREATED_NEW, status_code=201)
