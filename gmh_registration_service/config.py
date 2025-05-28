## begin license ##
#
# "WWFT Frontend" is the portal for an organisation to comply with WWFT regulations
#
# All rights reserved.
#
# Copyright (C) 2024-2025 Seecr (Seek You Too B.V.) http://seecr.nl
#
# This file is part of "WWFT Frontend"
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
