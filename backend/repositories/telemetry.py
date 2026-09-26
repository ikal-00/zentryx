"""Atomic, idempotent telemetry write and vehicle status update."""


def insert_telemetry(pool, payload):
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
                    %s, %s, %s,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                    %s, %s, %s, %s, %s
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
    return inserted is not None
