from flask import Blueprint, current_app


rutas = Blueprint("rutas", __name__, url_prefix="/v1")


@rutas.get("/routes")
def list_routes():
    pool = current_app.extensions["POOL"]
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    route_id,
                    name,
                    active,
                    line_id,
                    line_label,
                    service_id,
                    service_name,
                    origin_name,
                    destination_name,
                    direction_forward_label,
                    direction_reverse_label
                FROM routes
                ORDER BY name
                LIMIT 100 OFFSET 0;
                """
            )
            rows = cur.fetchall()

    return {
        "routes": [
            {
                "route_id": row[0],
                "name": row[1],
                "active": row[2],
                "line_id": row[3],
                "line_label": row[4],
                "service_id": row[5],
                "service_name": row[6],
                "origin_name": row[7],
                "destination_name": row[8],
                "direction_forward_label": row[9],
                "direction_reverse_label": row[10],
            }
            for row in rows
        ]
    }, 200


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
                WHERE rs.route_id = %s
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
                SELECT
                    station_id,
                    name,
                    ST_Y(position) AS lat,
                    ST_X(position) AS lon,
                    active
                FROM stations
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
