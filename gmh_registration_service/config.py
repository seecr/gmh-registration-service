## begin license ##
#
# Gemeenschappelijke Metadata Harvester (GMH) Registration Service
#  register NBN and urls
#
# Copyright (C) 2024-2025 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2025 Koninklijke Bibliotheek (KB) https://www.kb.nl
#
# This file is part of "GMH-Registration-Service"
#
# "GMH-Registration-Service" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "GMH-Registration-Service" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "GMH-Registration-Service"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

import json
import logging
from urllib.parse import urlparse

from configparser import ConfigParser


logger = logging.getLogger(__name__)


class Config:
    def __init__(self, data_path, development):
        self.data_path = data_path
        self.config_path = data_path / "config"

        cp = self.config_path / "config.json"
        config = json.loads(cp.read_text()) if cp.is_file() else {}
        self.development = development
        self.deproxy_ips = config.get("deproxy_ips", [])

        self.database_config = self._read_database_config()

    def _read_database_config(self):
        cp = ConfigParser()
        cp.read(self.config_path / "database.conf")
        return dict(cp.items("client"))
