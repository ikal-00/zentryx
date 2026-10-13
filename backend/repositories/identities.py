"""Read device assignments; token policy belongs to services."""


def device_assignment(pool, vehicle_id, device_id=None):
    if device_id is None:
        query = """
            SELECT d.device_id, d.token_hash, d.active, v.active
            FROM vehicles AS v
            JOIN devices AS d ON d.device_id = v.device_id
            WHERE v.vehicle_id = %s
        """
        params = (vehicle_id,)
    else:
        query = """
            SELECT d.device_id, d.token_hash, d.active, v.active
            FROM devices AS d
            JOIN vehicles AS v ON v.device_id = d.device_id
            WHERE d.device_id = %s AND v.vehicle_id = %s
        """
        params = (device_id, vehicle_id)

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            row = cur.fetchone()

    return row
