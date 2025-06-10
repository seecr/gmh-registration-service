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


class Database:
    def __init__(self, host, user, password, database):
        self._pool = MySQLConnectionPool(
            pool_reset_session=True,
            pool_size=5,
            host=host,
            user=user,
            password=password,
            database=database,
        )

    @contextmanager
    def cursor(self, commit=True):
        with self._pool.get_connection() as conn:
            with conn.cursor() as _cursor:
                yield _cursor
            if commit is True:
                conn.commit()

    def execute_statements(self, stmts):
        with self.cursor(commit=False) as cursor:
            for stmt in stmts:
                cursor.execute(stmt)

    def select_query(
        self,
        fields,
        from_stmt,
        where_stmt,
        values,
        order_by_stmt="",
        target_fields=None,
        conv=None,
    ):
        if callable(conv):
            result_fields = [conv(f) for f in fields]
        else:
            result_fields = target_fields or fields

        if len(result_fields) != len(fields):
            raise RuntimeError("result_fields and fields need to be same length")

        results = []
        select_stmt = ", ".join(fields)

        query = f"SELECT {select_stmt} FROM {from_stmt} WHERE {where_stmt}"
        if order_by_stmt != "":
            query = f"{query} ORDER BY {order_by_stmt}"

        with self.cursor(commit=False) as cursor:
            cursor.execute(query, values)
            for hit in cursor:
                results.append(dict(zip(result_fields, hit)))
        return results

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

    def get_locations(self, identifier, include_ltp):
        return self.select_query(
            ["L.location_url", "IL.isFailover"],
            from_stmt="identifier I JOIN identifier_location IL ON I.identifier_id = IL.identifier_id JOIN location L ON L.location_id = IL.location_id",
            where_stmt=(
                "I.identifier_value=%(identifier)s"
                + ("" if include_ltp else " AND IL.isFailover=0")
            ),
            order_by_stmt="IL.isFailover, IL.last_modified ASC",
            values=dict(identifier=unfragment(identifier)),
            target_fields=["uri", "ltp"],
        )

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
        with self.cursor() as cursor:
            for location in locations:
                cursor.execute(
                    "call addNbnLocation(%(identifier)s, %(location)s, %(registrant_id)s, %(isLTP)s)",
                    dict(
                        identifier=unfragment(identifier),
                        location=location,
                        registrant_id=user["registrant_id"],
                        isLTP=user["isLTP"],
                    ),
                )

    def delete_nbn_locations(self, identifier, user):
        with self.cursor() as cursor:
            cursor.execute(
                "call deleteNbnLocationsByRegistrantId(%(identifier)s, %(registrant_id)s, %(isLTP)s)",
                dict(
                    identifier=unfragment(identifier),
                    registrant_id=user["registrant_id"],
                    isLTP=user["isLTP"],
                ),
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
