from flask import Blueprint
from flask import current_app

rutas = Blueprint(
    "rutas",
    __name__,
    url_prefix="/v1/routes"
);

@rutas.get("/")
def rutasC():
    pool = current_app.extensions["POOL"];

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT route_id,name,active FROM routes  LIMIT 100 OFFSET 0;");
            rutas_R = cur.fetchall();

    payload = {
        "routes" : [
            {
                "route_id" : fila[0],
                "name" : fila[1],
                "active" : fila[2]
            }
            for fila in rutas_R
        ]
    }

    return payload;

@rutas.get("/v1/routes/<string:route_id>/stations")
def Station_R(route_id):
    pool = current_app.extensions["POOL"];

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    s.station_id,
                    s.name,
                    s.position,
                    s.active,
                    rs.stop_order
                FROM route_stations AS rs
                INNER JOIN stations AS s
                    ON s.station_id = rs.station_id
                WHERE rs.route_id = %s
                ORDER BY rs.stop_order;
            """, (route_id,));

            stations = cur.fetchall();

    payload = {
        "route_id": route_id,
        "stations": [
            {
                "station_id": fila[0],
                "name": fila[1],
                "position": fila[2],
                "active": fila[3],
                "stop_order": fila[4]
            }
            for fila in stations
        ]
    };

    return payload;