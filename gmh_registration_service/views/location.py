from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException

from gmh_registration_service.messages import NOT_FOUND
from gmh_registration_service.utils import get_user_by_token


def get_nbn_by_location(database, location):
    return database.select_query(
        ["I.identifier_value"],
        "identifier I JOIN identifier_location IL ON I.identifier_id = IL.identifier_id JOIN location L ON L.location_id = IL.location_id",
        "L.location_url = %(location)s;",
        dict(location=location),
        target_fields=["identifier_value"],
    )


async def location(request, database, **kwargs):
    # Raises HTTPException if no authorization or valid user
    get_user_by_token(request, database)

    location = request.path_params.get("location")
    if len(location.strip()) == 0:
        raise HTTPException(status_code=404, detail=NOT_FOUND)

    nbns = get_nbn_by_location(database, location)
    if len(nbns) == 0:
        raise HTTPException(status_code=404, detail=NOT_FOUND)
    return JSONResponse([each["identifier_value"] for each in nbns])
