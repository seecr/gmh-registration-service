import importlib.resources as pkg_resources

from pathlib import Path

package_name = Path(__file__).parent.stem

__all__ = ["testdata_path", "static_path", "templates_path", "global_config_path"]

_path = pkg_resources.files(package_name)
testdata_path = _path / "testdata"
static_path = _path / "static"
templates_path = _path / "templates"
global_config_path = _path / "config-data"
