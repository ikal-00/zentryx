import json

from flask import Blueprint, current_app, request


rutas = Blueprint("rutas", __name__, url_prefix="/v1")


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


def _route_payload(row):
    return {
        "route_id": row[0],
        "name": row[1],
        "active": row[2],
        "line_id": row[3],
        "line_label": row[4],
        "network_name": row[5],
        "service_id": row[6],
        "service_name": row[7],
        "origin_name": row[8],
        "destination_name": row[9],
        "direction_forward_label": row[10],
        "direction_reverse_label": row[11],
        "default_speed_mps": row[12],
    }


@rutas.get("/routes")
def list_routes():
    pool = current_app.extensions["POOL"]
    active_only = request.args.get("active", "true").lower() not in {"0", "false", "no"}
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
    return {"routes": [_route_payload(row) for row in rows]}, 200


@rutas.get("/routes/<string:route_id>")
def route_detail(route_id):
    pool = current_app.extensions["POOL"]
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

    if row is None:
        return {"error": "route_not_found"}, 404

    payload = _route_payload(row)
    geometry = json.loads(row[13]) if row[13] else None
    payload["path"] = (
        [
            {"lat": float(lat), "lon": float(lon)}
            for lon, lat in geometry.get("coordinates", [])
        ]
        if geometry and geometry.get("type") == "LineString"
        else []
    )
    return payload, 200


@rutas.get("/routes/<string:route_id>/stations")
def route_stations(route_id):
    pool = current_app.extensions["POOL"]
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM routes WHERE route_id = %s AND active = TRUE;",
                (route_id,),
            )
            if cur.fetchone() is None:
                return {"error": "route_not_found"}, 404

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

    return {
        "route_id": route_id,
        "stations": [
            {
                "station_id": row[0],
                "name": row[1],
                "position": {"lat": row[2], "lon": row[3]},
                "active": row[4],
                "order": row[5],
            }
            for row in rows
        ],
    }, 200


@rutas.get("/stations")
def list_stations():
    pool = current_app.extensions["POOL"]
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

    return {
        "stations": [
            {
                "station_id": row[0],
                "name": row[1],
                "position": {"lat": row[2], "lon": row[3]},
                "active": row[4],
            }
            for row in rows
        ]
    }, 200
