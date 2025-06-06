from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException

from gmh_registration_service.messages import NOT_FOUND
from gmh_registration_service.utils import get_user_by_token


async def location(request, database, **kwargs):
    # Raises HTTPException if no authorization or valid user
    get_user_by_token(request, database)

    location = request.path_params.get("location")
    if len(location.strip()) == 0:
        raise HTTPException(status_code=404, detail=NOT_FOUND)

    if len(nbns := database.get_nbn_by_location(location)) == 0:
        raise HTTPException(status_code=404, detail=NOT_FOUND)
    return JSONResponse([each["identifier_value"] for each in nbns])
