from flask import Blueprint
from flask import current_app

vehiculos = Blueprint(
    "vehiculos",
    __name__,
    url_prefix="/v1/vehicles"
);

@vehiculos.get("/")
def Vehiculos_C():
    pool = current_app.extensions["POOL"];

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    v.vehicle_id,
                    v.route_id,
                    v.status,
                    v.occupancy_level,
                    t.lat,
                    t.lon,
                    t.speed_mps,
                    t.accuracy_m,
                    t.heading_deg,
                    t.last_update
                FROM vehicles AS v
                LEFT JOIN vehicle_latest_telemetry AS t
                    ON t.vehicle_id = v.vehicle_id
                WHERE v.active = TRUE
                ORDER BY v.vehicle_id;
            """);

            vehicles = cur.fetchall();
    payload = {
        "vehicles": [
            {
                "vehicle_id": fila[0],
                "route_id": fila[1],
                "status": fila[2],
                "position": {
                    "lat": fila[4],
                    "lon": fila[5]
                },
                "speed_mps": fila[6],
                "accuracy_m": fila[7],
                "heading_deg": fila[8],
                "occupancy_level": fila[3],
                "last_update": fila[9].isoformat() if fila[9] else None
            }
            for fila in vehicles
        ]
    };

    return payload;

@vehiculos.get("/<string:vehicle_id>")
def VehicleR(vehicle_id):
    pool = current_app.extensions["POOL"];

    with pool.connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    v.vehicle_id,
                    v.route_id,
                    v.status,
                    v.occupancy_level,
                    t.lat,
                    t.lon,
                    t.speed_mps,
                    t.accuracy_m,
                    t.heading_deg,
                    t.last_update
                FROM vehicles AS v
                LEFT JOIN vehicle_latest_telemetry AS t
                    ON t.vehicle_id = v.vehicle_id
                WHERE v.vehicle_id = %s
                  AND v.active = TRUE;
            """, (vehicle_id,));

            fila = cur.fetchone();

    if fila is None:
        return {"error": "Vehicle not found"}, 404

    payload = {
        "vehicle_id": fila[0],
        "route_id": fila[1],
        "status": fila[2],
        "position": {
            "lat": fila[4],
            "lon": fila[5]
        },
        "speed_mps": fila[6],
        "accuracy_m": fila[7],
        "heading_deg": fila[8],
        "occupancy_level": fila[3],
        "last_update": fila[9].isoformat() if fila[9] else None
    };

    return payload;