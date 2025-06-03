def select_query(pool, fields, from_stmt, where_stmt, values, target_fields=None):
    if target_fields is None:
        target_fields = fields

    if len(target_fields) != len(fields):
        raise RuntimeError("itarget_fields and fields need to be same length")

    results = []
    select_stmt = ", ".join(fields)
    with pool.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT {select_stmt} FROM {from_stmt} WHERE {where_stmt}", values
            )
            for hit in cursor:
                results.append(dict(zip(target_fields, hit)))
    return results
