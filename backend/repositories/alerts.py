"""Read active alerts with server priority and optional scope."""


def list_alerts(pool, route_id=None, vehicle_id=None):
    clauses = ["active = TRUE"]
    params = []
    if route_id:
        clauses.append("(route_id = %s OR route_id IS NULL)")
        params.append(route_id)
    if vehicle_id:
        clauses.append("(vehicle_id = %s OR vehicle_id IS NULL)")
        params.append(vehicle_id)

    query = f"""
        SELECT alert_id, route_id, vehicle_id, type, message,
               severity, created_at, active
        FROM alerts
        WHERE {" AND ".join(clauses)}
        ORDER BY
            CASE severity WHEN 'critical' THEN 0 WHEN 'warning' THEN 1 ELSE 2 END,
            created_at DESC;
    """

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
    return rows
