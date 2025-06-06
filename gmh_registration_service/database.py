def select_query(
    pool,
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

    with pool.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, values)
            for hit in cursor:
                results.append(dict(zip(result_fields, hit)))
    return results


def get_user_by_token(pool, token):
    result = select_query(
        pool,
        ["R.prefix", "R.isLTP", "R.registrant_id", "R.registrant_groupid"],
        from_stmt="registrant R inner join credentials C ON R.registrant_id = C.registrant_id",
        where_stmt="C.token = %(token)s",
        values=dict(token=token),
        conv=lambda f: f.split(".", 1)[-1],
    )

    if len(result) > 1:
        raise RuntimeError("Multiple users with same token!")

    return result[0] if len(result) == 1 else None


def has_ltp_location(pool, identifier, org_prefix):
    registrant_id = get_registrant_id_by_org_prefix(pool, org_prefix)

    results = select_query(
        pool,
        ["IL.isFailover"],
        from_stmt="identifier_location IL JOIN identifier I ON IL.identifier_id = I.identifier_id JOIN identifier_registrant IR ON I.identifier_id = IR.identifier_id",
        where_stmt="IL.isFailover = %(isFailover)s AND I.identifier_value = %(identifier_value)s AND IR.registrant_id = %(registrant_id)s",
        values=dict(
            identifier_value=identifier, registrant_id=registrant_id, isFailover="1"
        ),
    )

    return len(results) > 0


def get_registrant_id_by_org_prefix(pool, org_prefix):
    registrant_id = 0
    result = select_query(
        pool,
        ["registrant_id"],
        from_stmt="registrant",
        where_stmt="prefix=%(prefix)s",
        values=dict(prefix=org_prefix),
    )

    if len(result) > 0:
        registrant_id = result[0]["registrant_id"]

    return registrant_id


def get_locations(pool, identifier, include_ltp):
    return select_query(
        pool,
        ["L.location_url", "IL.isFailover"],
        from_stmt="identifier I JOIN identifier_location IL ON I.identifier_id = IL.identifier_id JOIN location L ON L.location_id = IL.location_id",
        where_stmt=(
            "I.identifier_value=%(identifier)s"
            + ("" if include_ltp else " AND IL.isFailover=0")
        ),
        order_by_stmt="IL.isFailover, IL.last_modified ASC",
        values=dict(identifier=identifier),
        target_fields=["uri", "ltp"],
    )


def is_resolvable_identifier(pool, identifier):
    return (
        len(
            select_query(
                pool,
                ["I.identifier_id"],
                from_stmt="identifier I INNER JOIN identifier_location IL ON I.identifier_id=IL.identifier_id",
                where_stmt="I.identifier_value = %(identifier)s",
                values=dict(identifier=identifier),
                target_fields=["identifier_id"],
            )
        )
        > 0
    )


def add_nbn_locations(pool, identifier, locations, user):
    with pool.get_connection() as conn:
        with conn.cursor() as cursor:
            for location in locations:
                cursor.execute(
                    "call addNbnLocation(%(identifier)s, %(location)s, %(registrant_id)s, %(isLTP)s)",
                    dict(
                        identifier=identifier,
                        location=location,
                        registrant_id=user["registrant_id"],
                        isLTP=user["isLTP"],
                    ),
                )
        conn.commit()


def delete_nbn_locations(pool, identifier, user):
    with pool.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "call deleteNbnLocationsByRegistrantId(%(identifier)s, %(registrant_id)s, %(isLTP)s)",
                dict(
                    identifier=identifier,
                    registrant_id=user["registrant_id"],
                    isLTP=user["isLTP"],
                ),
            )
        conn.commit()
