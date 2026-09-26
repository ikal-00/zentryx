"""Opt-in demo provisioning; production requests never invoke this repository."""

import psycopg
from ..auth import hash_token


def bootstrap_demo(postgres_url, device_id, vehicle_id, route_id, token: str) -> int:
    if not postgres_url:
        raise RuntimeError("postgres_url is required")

    with psycopg.connect(postgres_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO devices (device_id, name, token_hash, active, updated_at)
                VALUES (%s, %s, %s, TRUE, NOW())
                ON CONFLICT (device_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    token_hash = EXCLUDED.token_hash,
                    active = TRUE,
                    updated_at = NOW();
                """,
                (device_id, "GPS demo compartido", hash_token(token)),
            )
            cur.execute(
                """
                INSERT INTO vehicles (
                    vehicle_id, display_name, route_id, device_id,
                    status, occupancy_level, active, updated_at
                ) VALUES (%s, %s, %s, %s, 'unknown', 'medium', TRUE, NOW())
                ON CONFLICT (vehicle_id) DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    route_id = EXCLUDED.route_id,
                    device_id = EXCLUDED.device_id,
                    occupancy_level = EXCLUDED.occupancy_level,
                    active = TRUE,
                    updated_at = NOW();
                """,
                (vehicle_id, "Unidad demo compartida", route_id, device_id),
            )
            cur.execute(
                """
                INSERT INTO alerts (
                    alert_id, route_id, vehicle_id, type, message, severity, active, resolved_at
                ) VALUES (
                    'alert-demo-shared', %s, %s, 'service',
                    'Servidor compartido Zentryx en modo de prueba', 'info', TRUE, NULL
                )
                ON CONFLICT (alert_id) DO UPDATE SET
                    route_id = EXCLUDED.route_id,
                    vehicle_id = EXCLUDED.vehicle_id,
                    type = EXCLUDED.type,
                    message = EXCLUDED.message,
                    severity = EXCLUDED.severity,
                    active = TRUE,
                    resolved_at = NULL;
                """,
                (route_id, vehicle_id),
            )
            cur.execute(
                "SELECT COALESCE(MAX(sequence), -1) + 1 FROM telemetry WHERE device_id = %s;",
                (device_id,),
            )
            sequence = int(cur.fetchone()[0])
        conn.commit()
    return sequence
