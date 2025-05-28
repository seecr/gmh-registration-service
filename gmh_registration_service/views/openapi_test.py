from ..test_utils import environment, environment_session

import yaml
from io import StringIO


async def test_openapi(environment):
    response = environment.client.get("/api/v1/openapi.yaml")
    assert response.status_code == 200
    parsed = yaml.safe_load(StringIO(response.text))
    assert list(parsed.keys()) == [
        "openapi",
        "info",
        "externalDocs",
        "paths",
        "servers",
        "tags",
        "components",
    ]
