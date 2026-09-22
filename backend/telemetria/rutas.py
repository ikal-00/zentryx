from flask import Blueprint
from flask import current_app
from flask import request


telemetria = Blueprint(
    "telemetria",
    __name__,
    url_prefix="/"
)

@telemetria.post("/v1/telemetry")
def Telemetry():

    # ---------------------------------------
    # 1. Validar Content-Type
    # ---------------------------------------

    if not request.is_json:
        return {
            "error": "invalid_content_type"
        }, 400 ;

    # ---------------------------------------
    # 2. Obtener y validar JSON
    # ---------------------------------------

    data = request.get_json(silent=True);
    if data is None:
        return {
            "error": "invalid_json"
        }, 400 ;

    # ---------------------------------------
    # 3. Obtener Authorization
    # ---------------------------------------

    authorization = request.headers.get("Authorization")

    if not authorization:
        return {
            "error": "missing_authorization"
        }, 401

    try:
        scheme, auth = authorization.split(" ", 1)
    except ValueError:
        return {
            "error": "invalid_authorization"
        }, 401

    if scheme != "Device":
        return {
            "error": "invalid_authorization"
        }, 401

    # ---------------------------------------
    # 4. Obtener pool
    # ---------------------------------------

    pool = current_app.extensions["POOL"]

    # ---------------------------------------
    # 5. Validar campos básicos
    # ---------------------------------------

    required = [
        "device_id",
        "vehicle_id",
        "seq",
        "position",
        "observed_at"
    ]

    if any(field not in data for field in required):
        return {
            "error": "invalid_data"
        }, 422 ;

    # ---------------------------------------
    # 6. Comprobar device + vehicle
    # ---------------------------------------

    with pool.connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    d.device_id,
                    v.vehicle_id
                FROM devices AS d

                JOIN vehicles AS v
                    ON v.device_id = d.device_id

                WHERE d.device_id = %s
                  AND v.vehicle_id = %s
                  AND d.token_hash = %s
            """, (
                data["device_id"],
                data["vehicle_id"],
                auth
            ))

            resp = cur.fetchone()

    # ---------------------------------------
    # 7. Device / vehicle inexistente
    # ---------------------------------------

    if resp is None:
        return {
            "error": "device_or_vehicle_not_found"
        }, 404

    # ---------------------------------------
    # 8. Aceptar telemetría
    # ---------------------------------------

    with pool.connection() as conn:
            with conn.cursor() as cur:
    
                cur.execute("""
                    SELECT
                        d.device_id,
                        v.vehicle_id
                    FROM devices AS d
    
                    JOIN vehicles AS v
                        ON v.device_id = d.device_id
    
                    WHERE d.device_id = %s
                      AND v.vehicle_id = %s
                      AND d.token_hash = %s
                """, (
                    data["device_id"],
                    data["vehicle_id"],
                    auth
                ));
    
                resp = cur.fetchone();
    return {
        "accepted": True,
        "device_id": data["device_id"],
        "seq": data["seq"]
    }, 202

@telemetria.get("/v1/alerts")
def Alert():
    pool = current_app.extensions["POOL"];

    with pool.connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    alert_id,
                    route_id,
                    vehicle_id,
                    type,
                    message,
                    severity,
                    created_at,
                    active
                FROM alerts
                WHERE active = TRUE
                  AND created_at >= CURRENT_DATE
                  AND created_at < CURRENT_DATE + INTERVAL '1 day'
                ORDER BY created_at DESC;
            """);

            rows = cur.fetchall();

    if rows is None:
        return 202;

    alerts = [];

    for row in rows:
        alerts.append({
            "alert_id": row[0],
            "route_id": row[1],
            "vehicle_id": row[2],
            "type": row[3],
            "message": row[4],
            "severity": row[5],
            "created_at": row[6].isoformat(),
            "active": row[7]
        });

    return {
        "alerts": alerts
    }, 200 ;

@telemetria.post("/v1/incidents")
def Incident():
    if not request.is_json:
        return {
            "error": "invalid_content_type"
        }, 400 ;    

    data = request.get_json(silent=True);
    if data is None:
            return {
                "error": "invalid_json"
            }, 400 ;

    authorization = request.headers.get("Authorization");

    if not authorization:
            return {
                "error": "missing_authorization"
            }, 401 ;

    try:
        scheme, auth = authorization.split(" ", 1)
    except ValueError:
        return {
            "error": "invalid_authorization"
        }, 401 ;

    if scheme != "Device":
        return {
            "error": "invalid_authorization"
        }, 401 ;

    pool = current_app.extensions["POOL"];

    required = [
        "vehicle_id",
        "type",
        "description",
        "position",
        "observed_at"
    ];

    if any(field not in data for field in required):
            return {
                "error": "invalid_data"
            }, 422 ;

    with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        d.device_id,
                        v.vehicle_id
                    FROM devices AS d
    
                    JOIN vehicles AS v
                        ON v.device_id = d.device_id
    
                    WHERE d.device_id = %s
                      AND v.vehicle_id = %s
                      AND d.token_hash = %s
                """, (
                    data["device_id"],
                    data["vehicle_id"],
                    auth
                ));
    
                resp = cur.fetchone();

    if resp is None:
            return {
                "error": "device_or_vehicle_not_found"
            }, 404 ;

    with pool.connection() as conn:
                with conn.cursor() as cur:
        
                    cur.execute("""
                        SELECT
                            d.device_id,
                            v.vehicle_id
                        FROM devices AS d
        
                        JOIN vehicles AS v
                            ON v.device_id = d.device_id
        
                        WHERE d.device_id = %s
                          AND v.vehicle_id = %s
                          AND d.token_hash = %s
                    """, (
                        data["device_id"],
                        data["vehicle_id"],
                        auth
                    ));
        
                    resp = cur.fetchone();