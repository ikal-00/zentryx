import json

from flask import Blueprint, current_app

from ..navigation import RouteNavigator


vehiculos = Blueprint("vehiculos", __name__, url_prefix="/v1")


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


def _load_route_context(pool, route_id, cache):
    if not route_id:
        return None
    if route_id in cache:
        return cache[route_id]

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
                cache[route_id] = None
                return None

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

    geometry = json.loads(route_row[0])
    coordinates = [
        (float(lat), float(lon))
        for lon, lat in geometry.get("coordinates", [])
    ]
    stations = [
        {
            "station_id": row[0],
            "name": row[1],
            "stop_order": row[2],
            "lat": row[3],
            "lon": row[4],
        }
        for row in station_rows
    ]
    if len(coordinates) < 2 or not stations:
        cache[route_id] = None
        return None

    context = {
        "navigator": RouteNavigator(coordinates, stations),
        "forward_label": route_row[1],
        "reverse_label": route_row[2],
        "default_speed_mps": route_row[3] or 6.0,
    }
    cache[route_id] = context
    return context


def _serialize_vehicle(row, pool, route_cache):
    (
        vehicle_id,
        route_id,
        status,
        occupancy_level,
        lat,
        lon,
        speed_mps,
        accuracy_m,
        heading_deg,
        last_update,
        history,
        smoothed_speed_mps,
    ) = row

    navigation = None
    context = _load_route_context(pool, route_id, route_cache)
    if context is not None and lat is not None and lon is not None:
        history = history or []
        # First history item is normally the current packet. Exclude points that
        # project to the exact current sample from direction inference.
        older_history = history[1:] if len(history) > 1 else []
        result = context["navigator"].navigation(
            lat=lat,
            lon=lon,
            history=older_history,
            heading_deg=heading_deg,
            speed_mps=speed_mps,
            smoothed_speed_mps=smoothed_speed_mps,
            default_speed_mps=context["default_speed_mps"],
        )
        direction = (
            "forward"
            if result.direction == 1
            else "reverse"
            if result.direction == -1
            else "unknown"
        )
        direction_label = (
            context["forward_label"]
            if result.direction == 1
            else context["reverse_label"]
            if result.direction == -1
            else None
        )
        navigation = {
            "direction": direction,
            "direction_source": result.direction_source,
            "direction_label": direction_label,
            "progress_m": round(result.progress_m, 2)
            if result.progress_m is not None
            else None,
            "route_length_m": round(result.route_length_m, 2),
            "next_station": (
                {
                    "station_id": result.next_station_id,
                    "name": result.next_station_name,
                }
                if result.next_station_id is not None
                else None
            ),
            "distance_remaining_m": (
                round(result.distance_remaining_m, 2)
                if result.distance_remaining_m is not None
                else None
            ),
            "eta_seconds": (
                round(result.eta_seconds, 1)
                if result.eta_seconds is not None
                else None
            ),
            "eta_speed_mps": (
                round(result.eta_speed_mps, 2)
                if result.eta_speed_mps is not None
                else None
            ),
        }

    return {
        "vehicle_id": vehicle_id,
        "route_id": route_id,
        "status": status,
        "position": {"lat": lat, "lon": lon}
        if lat is not None and lon is not None
        else None,
        "speed_mps": speed_mps,
        "accuracy_m": accuracy_m,
        "heading_deg": heading_deg,
        "occupancy_level": occupancy_level,
        "last_update": last_update.isoformat().replace("+00:00", "Z")
        if last_update
        else None,
        "navigation": navigation,
    }


@vehiculos.get("/vehicles")
def list_vehicles():
    pool = current_app.extensions["POOL"]
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(VEHICLE_QUERY + " ORDER BY v.vehicle_id;")
            rows = cur.fetchall()

    route_cache = {}
    return {
        "vehicles": [_serialize_vehicle(row, pool, route_cache) for row in rows]
    }, 200


@vehiculos.get("/vehicles/<string:vehicle_id>")
def get_vehicle(vehicle_id):
    pool = current_app.extensions["POOL"]
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(VEHICLE_QUERY + " AND v.vehicle_id = %s;", (vehicle_id,))
            row = cur.fetchone()

    if row is None:
        return {"error": "vehicle_not_found"}, 404

    return _serialize_vehicle(row, pool, {}), 200
