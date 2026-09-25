from uuid import uuid4

from flask import Blueprint, current_app, request

from ..api_utils import (
    PayloadValidationError,
    authenticate_vehicle_device,
    parse_device_authorization,
    validate_incident_payload,
    validate_telemetry_payload,
)


telemetria = Blueprint("telemetria", __name__, url_prefix="/v1")


def _json_body():
    if not request.is_json:
        return None, ({"error": "invalid_content_type"}, 400)
    data = request.get_json(silent=True)
    if data is None:
        return None, ({"error": "invalid_json"}, 400)
    return data, None


def _device_token():
    try:
        return parse_device_authorization(request.headers.get("Authorization")), None
    except PayloadValidationError as exc:
        return None, ({"error": exc.message}, 401)


def _validation_error(exc):
    return {
        "error": "invalid_data",
        "field": exc.field,
        "detail": exc.message,
    }, 422


@telemetria.post("/telemetry")
def post_telemetry():
    data, error = _json_body()
    if error:
        return error

    token, error = _device_token()
    if error:
        return error

    try:
        payload = validate_telemetry_payload(data)
    except PayloadValidationError as exc:
        return _validation_error(exc)

    pool = current_app.extensions["POOL"]
    _, auth_error = authenticate_vehicle_device(
        pool,
        vehicle_id=payload["vehicle_id"],
        device_id=payload["device_id"],
        token=token,
    )
    if auth_error == "invalid_authorization":
        return {"error": auth_error}, 401
    if auth_error:
        return {"error": auth_error}, 404

    position = payload["position"]
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO telemetry (
                    device_id,
                    vehicle_id,
                    sequence,
                    position,
                    speed_mps,
                    accuracy_m,
                    heading_deg,
                    satellites,
                    observed_at
                ) VALUES (
                    %s,
                    %s,
                    %s,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                ON CONFLICT (device_id, sequence) DO NOTHING
                RETURNING id;
                """,
                (
                    payload["device_id"],
                    payload["vehicle_id"],
                    payload["seq"],
                    position["lon"],
                    position["lat"],
                    position["speed_mps"],
                    position["accuracy_m"],
                    position["heading_deg"],
                    position["satellites"],
                    payload["observed_at"],
                ),
            )
            inserted = cur.fetchone()

            if inserted is not None:
                cur.execute(
                    """
                    UPDATE vehicles
                    SET status = 'online', updated_at = NOW()
                    WHERE vehicle_id = %s;
                    """,
                    (payload["vehicle_id"],),
                )

    response = {
        "accepted": True,
        "device_id": payload["device_id"],
        "seq": payload["seq"],
    }
    if inserted is None:
        response["duplicate"] = True
    return response, 202


@telemetria.get("/alerts")
def list_alerts():
    pool = current_app.extensions["POOL"]
    route_id = request.args.get("route_id")
    vehicle_id = request.args.get("vehicle_id")

    clauses = ["active = TRUE"]
    params = []
    if route_id:
        clauses.append("(route_id = %s OR route_id IS NULL)")
        params.append(route_id)
    if vehicle_id:
        clauses.append("(vehicle_id = %s OR vehicle_id IS NULL)")
        params.append(vehicle_id)

    query = f"""
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
        WHERE {' AND '.join(clauses)}
        ORDER BY created_at DESC;
    """

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, tuple(params))
            rows = cur.fetchall()

    return {
        "alerts": [
            {
                "alert_id": row[0],
                "route_id": row[1],
                "vehicle_id": row[2],
                "type": row[3],
                "message": row[4],
                "severity": row[5],
                "created_at": row[6].isoformat().replace("+00:00", "Z"),
                "active": row[7],
            }
            for row in rows
        ]
    }, 200


@telemetria.post("/incidents")
def create_incident():
    data, error = _json_body()
    if error:
        return error

    token, error = _device_token()
    if error:
        return error

    try:
        payload = validate_incident_payload(data)
    except PayloadValidationError as exc:
        return _validation_error(exc)

    pool = current_app.extensions["POOL"]
    _, auth_error = authenticate_vehicle_device(
        pool,
        vehicle_id=payload["vehicle_id"],
        token=token,
    )
    if auth_error == "invalid_authorization":
        return {"error": auth_error}, 401
    if auth_error:
        return {"error": auth_error}, 404

    incident_id = f"incident-{uuid4().hex[:12]}"
    position = payload["position"]
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO incidents (
                    incident_id,
                    vehicle_id,
                    type,
                    description,
                    position,
                    observed_at
                ) VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                    %s
                );
                """,
                (
                    incident_id,
                    payload["vehicle_id"],
                    payload["type"],
                    payload["description"],
                    position["lon"],
                    position["lat"],
                    payload["observed_at"],
                ),
            )

    return {"incident_id": incident_id, "created": True}, 201
