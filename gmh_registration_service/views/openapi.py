from starlette.responses import FileResponse

from .._path import static_path


#
# Test at: https://editor.swagger.io/
#
async def openapi(request, **_):
    return FileResponse(
        static_path / "openapi.yaml",
        media_type="text/yaml",
        headers={"Access-Control-Allow-Origin": "https://editor.swagger.io"},
    )
