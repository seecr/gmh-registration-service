from starlette.responses import PlainTextResponse, JSONResponse
from starlette.exceptions import HTTPException

from gmh_registration_service.messages import (
    INVALID_AUTH_INFO,
    BAD_REQUEST,
    URN_NBN_FORBIDDEN,
    URN_NBN_FORBIDDEN2,
    URN_NBN_INVALID,
    URN_NBN_LOCATION_INVALID,
    URN_NBN_NOT_FOUND,
    URN_NBN_CONFLICT,
    SUCCESS_CREATED_NEW,
    SUCCESS_UPDATED,
)

from gmh_registration_service.utils import (
    valid_urn_nbn,
    valid_location,
    get_user_by_token,
    parse_body_as_json,
)


async def _nbn_get_locations_by_identifier(request, database, urn_nbn, format_answer):
    user = get_user_by_token(request, database)

    if not valid_urn_nbn(urn_nbn):
        raise HTTPException(status_code=400, detail=URN_NBN_INVALID)

    if not urn_nbn.lower().startswith(
        user["prefix"].lower()
    ) and not database.has_ltp_location(identifier=urn_nbn, org_prefix=user["prefix"]):
        raise HTTPException(status_code=403, detail=URN_NBN_FORBIDDEN)

    if (
        len(locations := database.get_locations(identifier=urn_nbn, include_ltp=True))
        == 0
    ):
        raise HTTPException(status_code=404, detail=URN_NBN_NOT_FOUND)

    return JSONResponse(format_answer(urn_nbn, locations))


async def nbn_get(request, database, **kwargs):
    def format_answer(identifier, locations):
        return {
            "identifier": identifier,
            "locations": [location["uri"] for location in locations],
        }

    return await _nbn_get_locations_by_identifier(
        request, database, request.path_params.get("identifier"), format_answer
    )


async def nbn_get_locations(request, database, **kwargs):
    def format_answer(identifier, locations):
        return [location["uri"] for location in locations]

    return await _nbn_get_locations_by_identifier(
        request, database, request.path_params.get("identifier"), format_answer
    )


def _validate_identifier_and_locations(user, identifier, locations):
    # Validate identifier
    if not valid_urn_nbn(identifier):
        raise HTTPException(status_code=400, detail=URN_NBN_LOCATION_INVALID)

    # Validate locations
    for location in locations:
        if not valid_location(location):
            raise HTTPException(status_code=400, detail=URN_NBN_LOCATION_INVALID)

    # Prefix match registrant prefix with identifier; Forbidden is no match and user is not LTP
    if (
        not identifier.lower().startswith(user["prefix"].lower())
        and not bool(user["isLTP"]) is True
    ):
        raise HTTPException(status_code=403, detail=URN_NBN_FORBIDDEN2)


async def nbn(request, database, **kwargs):
    user = get_user_by_token(request, database)
    body = await parse_body_as_json(request)

    identifier = body.get("identifier")
    locations = body.get("locations")

    _validate_identifier_and_locations(user, identifier, locations)

    # Determine if identifier is resolvable (already has locations associated)
    if database.is_resolvable_identifier(identifier):
        raise HTTPException(status_code=409, detail=URN_NBN_CONFLICT)

    database.add_nbn_locations(identifier, locations, user)
    return PlainTextResponse(SUCCESS_CREATED_NEW, status_code=201)


async def nbn_update(request, database, **kwargs):
    user = get_user_by_token(request, database)
    body = await parse_body_as_json(request)

    identifier = request.path_params["identifier"]
    locations = body

    _validate_identifier_and_locations(user, identifier, locations)

    # Determine if identifier is resolvable (already has locations associated)
    if database.is_resolvable_identifier(identifier):
        database.delete_nbn_locations(identifier, user)
        database.add_nbn_locations(identifier, locations, user)
        return PlainTextResponse(SUCCESS_UPDATED, status_code=200)

    database.add_nbn_locations(identifier, locations, user)
    return PlainTextResponse(SUCCESS_CREATED_NEW, status_code=201)
