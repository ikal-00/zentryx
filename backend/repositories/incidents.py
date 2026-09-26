"""Persist an authorized driver incident."""


def insert_incident(pool, payload, driver_id, incident_id):
    position = payload["position"]
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO incidents (
                    incident_id,
                    vehicle_id,
                    driver_id,
                    type,
                    description,
                    position,
                    observed_at
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                    %s
                );
                """,
                (
                    incident_id,
                    payload["vehicle_id"],
                    driver_id,
                    payload["type"],
                    payload["description"],
                    position["lon"],
                    position["lat"],
                    payload["observed_at"],
                ),
            )
