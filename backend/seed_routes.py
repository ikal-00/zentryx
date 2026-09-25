"""Import Zentryx GeoJSON route assets into PostgreSQL/PostGIS.

Usage from repository root:
    POSTGRES_URL=... python -m backend.seed_routes
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg


ROOT = Path(__file__).resolve().parents[1]
ROUTE_PATH = ROOT / "app" / "assets" / "routes" / "l2_ordinary_route.geojson"
STATIONS_PATH = ROOT / "app" / "assets" / "routes" / "l2_ordinary_stations.geojson"


def _load(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def seed_l2(conn) -> dict[str, int | str]:
    route_data = _load(ROUTE_PATH)
    station_data = _load(STATIONS_PATH)

    route_features = [
        feature
        for feature in route_data.get("features", [])
        if feature.get("geometry", {}).get("type") == "LineString"
    ]
    if len(route_features) != 1:
        raise ValueError("L2 route asset must contain exactly one LineString")

    route_feature = route_features[0]
    props = route_feature.get("properties", {})
    route_id = str(props["route_id"])
    geometry_json = json.dumps(route_feature["geometry"], ensure_ascii=False)

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO routes (
                route_id, name, line_id, line_label, network_name,
                service_id, service_name, origin_name, destination_name,
                direction_forward_label, direction_reverse_label,
                default_speed_mps, path, active, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s,
                ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326),
                TRUE, NOW()
            )
            ON CONFLICT (route_id) DO UPDATE SET
                name = EXCLUDED.name,
                line_id = EXCLUDED.line_id,
                line_label = EXCLUDED.line_label,
                network_name = EXCLUDED.network_name,
                service_id = EXCLUDED.service_id,
                service_name = EXCLUDED.service_name,
                origin_name = EXCLUDED.origin_name,
                destination_name = EXCLUDED.destination_name,
                direction_forward_label = EXCLUDED.direction_forward_label,
                direction_reverse_label = EXCLUDED.direction_reverse_label,
                default_speed_mps = EXCLUDED.default_speed_mps,
                path = EXCLUDED.path,
                active = TRUE,
                updated_at = NOW();
            """,
            (
                route_id,
                props.get("name", "Mexibús Línea 2"),
                props.get("line_id"),
                props.get("line_label"),
                props.get("network_name"),
                props.get("service_id"),
                props.get("service_name"),
                props.get("origin_name"),
                props.get("destination_name"),
                props.get("direction_forward_label"),
                props.get("direction_reverse_label"),
                6.0,
                geometry_json,
            ),
        )

        stations = []
        for feature in station_data.get("features", []):
            if feature.get("geometry", {}).get("type") != "Point":
                continue
            station_props = feature.get("properties", {})
            lon, lat = feature["geometry"]["coordinates"]
            stations.append(
                (
                    str(station_props["station_id"]),
                    str(station_props["name"]),
                    int(station_props["stop_order"]),
                    float(lon),
                    float(lat),
                )
            )

        stations.sort(key=lambda item: item[2])
        expected = list(range(1, len(stations) + 1))
        if [item[2] for item in stations] != expected:
            raise ValueError("Station stop_order is incomplete or duplicated")

        for station_id, name, _, lon, lat in stations:
            cur.execute(
                """
                INSERT INTO stations (station_id, name, position, active, updated_at)
                VALUES (
                    %s, %s,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                    TRUE, NOW()
                )
                ON CONFLICT (station_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    position = EXCLUDED.position,
                    active = TRUE,
                    updated_at = NOW();
                """,
                (station_id, name, lon, lat),
            )

        cur.execute("DELETE FROM route_stations WHERE route_id = %s;", (route_id,))
        cur.executemany(
            """
            INSERT INTO route_stations (route_id, station_id, stop_order)
            VALUES (%s, %s, %s);
            """,
            [(route_id, station_id, stop_order) for station_id, _, stop_order, _, _ in stations],
        )

    conn.commit()
    return {"route_id": route_id, "stations": len(stations)}


def main():
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        raise RuntimeError("POSTGRES_URL is required")
    with psycopg.connect(postgres_url) as conn:
        result = seed_l2(conn)
    print(f"Seeded {result['route_id']} with {result['stations']} stations")


if __name__ == "__main__":
    main()
