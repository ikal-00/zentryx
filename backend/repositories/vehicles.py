"""Vehicle telemetry snapshots and route context from PostGIS."""

VEHICLE_QUERY = """
    SELECT
        v.vehicle_id,
        v.route_id,
        CASE
            WHEN t.last_update IS NULL THEN 'unknown'
            WHEN t.last_update >= NOW() - INTERVAL '30 seconds' THEN 'online'
            ELSE 'offline'
        END AS derived_status,
        v.occupancy_level,
        t.lat,
        t.lon,
        t.speed_mps,
        t.accuracy_m,
        t.heading_deg,
        t.last_update,
        recent.history,
        recent.smoothed_speed_mps
    FROM vehicles AS v
    LEFT JOIN vehicle_latest_telemetry AS t
        ON t.vehicle_id = v.vehicle_id
    LEFT JOIN LATERAL (
        SELECT
            jsonb_agg(
                jsonb_build_object(
                    'lat', ST_Y(sample.position),
                    'lon', ST_X(sample.position),
                    'speed_mps', sample.speed_mps,
                    'observed_at', sample.observed_at
                )
                ORDER BY sample.observed_at DESC, sample.id DESC
            ) AS history,
            AVG(sample.speed_mps) FILTER (
                WHERE sample.speed_mps IS NOT NULL
                  AND sample.speed_mps >= 0
            ) AS smoothed_speed_mps
        FROM (
            SELECT id, position, speed_mps, observed_at
            FROM telemetry
            WHERE vehicle_id = v.vehicle_id
              AND observed_at >= NOW() - INTERVAL '90 seconds'
            ORDER BY observed_at DESC, id DESC
            LIMIT 30
        ) AS sample
    ) AS recent ON TRUE
    WHERE v.active = TRUE
"""


def list_vehicles(pool):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(VEHICLE_QUERY + " ORDER BY v.vehicle_id;")
            return cur.fetchall()


def get_vehicle(pool, vehicle_id):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(VEHICLE_QUERY + " AND v.vehicle_id = %s;", (vehicle_id,))
            return cur.fetchone()


def route_context(pool, route_id):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    ST_AsGeoJSON(path),
                    direction_forward_label,
                    direction_reverse_label,
                    default_speed_mps
                FROM routes
                WHERE route_id = %s AND active = TRUE;
                """,
                (route_id,),
            )
            route_row = cur.fetchone()
            if route_row is None or route_row[0] is None:
                return None, []

            cur.execute(
                """
                SELECT
                    s.station_id,
                    s.name,
                    rs.stop_order,
                    ST_Y(s.position),
                    ST_X(s.position)
                FROM route_stations AS rs
                JOIN stations AS s ON s.station_id = rs.station_id
                WHERE rs.route_id = %s AND s.active = TRUE
                ORDER BY rs.stop_order;
                """,
                (route_id,),
            )
            station_rows = cur.fetchall()

    return route_row, station_rows
