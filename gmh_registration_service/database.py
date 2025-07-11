## begin license ##
#
# Gemeenschappelijke Metadata Harvester (GMH) Registration Service
#  register NBN and urls
#
# Copyright (C) 2025 Koninklijke Bibliotheek (KB) https://www.kb.nl
# Copyright (C) 2025 Seecr (Seek You Too B.V.) https://seecr.nl
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

from mysql.connector.pooling import MySQLConnectionPool

from contextlib import contextmanager
from .utils import unfragment

import bcrypt

import gmh_common.database


class Database(gmh_common.database.Database):
    def get_user_by_token(self, token):
        result = self.select_query(
            ["R.prefix", "R.isLTP", "R.registrant_id", "R.registrant_groupid"],
            from_stmt="registrant R inner join credentials C ON R.registrant_id = C.registrant_id",
            where_stmt="C.token = %(token)s",
            values=dict(token=token),
            conv=lambda f: f.split(".", 1)[-1],
        )

        if len(result) > 1:
            raise RuntimeError("Multiple users with same token!")

        return result[0] if len(result) == 1 else None

    def has_ltp_location(self, identifier, org_prefix):
        registrant_id = self.get_registrant_id_by_org_prefix(org_prefix)

        results = self.select_query(
            ["IL.isFailover"],
            from_stmt="identifier_location IL JOIN identifier I ON IL.identifier_id = I.identifier_id JOIN identifier_registrant IR ON I.identifier_id = IR.identifier_id",
            where_stmt="IL.isFailover = %(isFailover)s AND I.identifier_value = %(identifier_value)s AND IR.registrant_id = %(registrant_id)s",
            values=dict(
                identifier_value=identifier, registrant_id=registrant_id, isFailover="1"
            ),
        )

        return len(results) > 0

    def get_registrant_id_by_org_prefix(self, org_prefix):
        registrant_id = 0
        result = self.select_query(
            ["registrant_id"],
            from_stmt="registrant",
            where_stmt="prefix=%(prefix)s",
            values=dict(prefix=org_prefix),
        )

        if len(result) > 0:
            registrant_id = result[0]["registrant_id"]

        return registrant_id

    def get_registrant_id_by_groupid(self, groupid):
        registrant_id = None
        result = self.select_query(
            ["registrant_id"],
            from_stmt="registrant",
            where_stmt="registrant_groupid=%(groupid)s",
            values=dict(groupid=groupid),
        )

        if len(result) > 0:
            registrant_id = result[0]["registrant_id"]

        return registrant_id

    def get_credentials_by_registrant_id(self, registrant_id):
        response = None
        result = self.select_query(
            ["credentials_id"],
            from_stmt="credentials",
            where_stmt="registrant_id=%(registrant_id)s",
            values=dict(registrant_id=registrant_id),
        )

        if len(result) > 0:
            response = result[0]["credentials_id"]

        return response

    def is_resolvable_identifier(self, identifier):
        return (
            len(
                self.select_query(
                    ["I.identifier_id"],
                    from_stmt="identifier I INNER JOIN identifier_location IL ON I.identifier_id=IL.identifier_id",
                    where_stmt="I.identifier_value = %(identifier)s",
                    values=dict(identifier=unfragment(identifier)),
                    target_fields=["identifier_id"],
                )
            )
            > 0
        )

    def add_nbn_locations(self, identifier, locations, user):
        return super().add_nbn_locations(
            identifier,
            locations,
            registrant_id=user["registrant_id"],
            isLTP=user["isLTP"],
        )

    def delete_nbn_locations(self, identifier, user):
        return super().delete_nbn_locations(
            identifier,
            registrant_id=user["registrant_id"],
            isLTP=user["isLTP"],
        )

    def get_nbn_by_location(self, location):
        return self.select_query(
            ["I.identifier_value"],
            "identifier I JOIN identifier_location IL ON I.identifier_id = IL.identifier_id JOIN location L ON L.location_id = IL.location_id",
            "L.location_url = %(location)s;",
            dict(location=location),
            target_fields=["identifier_value"],
        )

    def update_token(self, token, credentials_id):
        with self.cursor() as cursor:
            cursor.execute(
                "UPDATE `credentials` SET `token`=%(token)s WHERE `credentials_id` = %(credentials_id)s",
                dict(token=token, credentials_id=credentials_id),
            )

    def validate_user_credentials(self, username, password):
        if username is None or password is None:
            return None

        matching_credentials = self.select_query(
            ["credentials_id", "password"],
            "credentials",
            "`username` = %(username)s;",
            dict(username=username),
        )
        if len(matching_credentials) != 1:
            return None

        credentials = matching_credentials[0]

        if (
            bcrypt.checkpw(
                password.encode("utf-8"), credentials["password"].encode("utf-8")
            )
            is False
        ):
            return None

        return credentials["credentials_id"]

    def set_password(self, groupid, username, password):
        if (registrant_id := self.get_registrant_id_by_groupid(groupid)) is None:
            raise RuntimeError(f"Registrant with groupid '{groupid}' not found")

        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        if (
            credentials_id := self.get_credentials_by_registrant_id(registrant_id)
        ) is None:
            with self.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO credentials (registrant_id, username, password) VALUES (%(registrant_id)s, %(username)s, %(password)s)",
                    dict(
                        registrant_id=registrant_id,
                        username=username,
                        password=hashed_password,
                    ),
                )
        else:
            with self.cursor() as cursor:
                cursor.execute(
                    "UPDATE `credentials` SET `username`=%(username)s, `password`=%(password)s WHERE `credentials_id` = %(credentials_id)s",
                    dict(
                        username=username,
                        password=hashed_password,
                        credentials_id=credentials_id,
                    ),
                )
