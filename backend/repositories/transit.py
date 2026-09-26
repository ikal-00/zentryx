"""PostGIS reads for routes and stations."""

ROUTE_COLUMNS = """
    route_id,
    name,
    active,
    line_id,
    line_label,
    network_name,
    service_id,
    service_name,
    origin_name,
    destination_name,
    direction_forward_label,
    direction_reverse_label,
    default_speed_mps
"""


def list_routes(pool, active_only=True):
    where = "WHERE active = TRUE" if active_only else ""
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT {ROUTE_COLUMNS}
                FROM routes
                {where}
                ORDER BY line_label NULLS LAST, service_name NULLS LAST, name
                LIMIT 100;
                """
            )
            rows = cur.fetchall()
    return rows


def route_detail(pool, route_id):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT {ROUTE_COLUMNS}, ST_AsGeoJSON(path)
                FROM routes
                WHERE route_id = %s AND active = TRUE;
                """,
                (route_id,),
            )
            row = cur.fetchone()
    return row


def route_stations(pool, route_id):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM routes WHERE route_id = %s AND active = TRUE;",
                (route_id,),
            )
            if cur.fetchone() is None:
                return None

            cur.execute(
                """
                SELECT
                    s.station_id,
                    s.name,
                    ST_Y(s.position) AS lat,
                    ST_X(s.position) AS lon,
                    s.active,
                    rs.stop_order
                FROM route_stations AS rs
                JOIN stations AS s ON s.station_id = rs.station_id
                WHERE rs.route_id = %s AND s.active = TRUE
                ORDER BY rs.stop_order;
                """,
                (route_id,),
            )
            rows = cur.fetchall()
    return rows


def list_stations(pool):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT station_id, name, ST_Y(position), ST_X(position), active
                FROM stations
                WHERE active = TRUE
                ORDER BY name
                LIMIT 1000;
                """
            )
            rows = cur.fetchall()
    return rows
