"""Shared development simulator for the Zentryx API.

This module is intentionally opt-in through the Docker Compose ``demo`` profile.
It creates a dedicated demo device/vehicle and an active test alert, then sends
fresh telemetry through the real HTTP API so route projection, direction, ETA,
offline handling and alerts can be tested end to end.
"""

from __future__ import annotations

import json
import math
import os
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import psycopg

from .api_utils import hash_token


ROOT = Path(__file__).resolve().parents[1]
ROUTE_PATH = ROOT / "app" / "assets" / "routes" / "l2_ordinary_route.geojson"

DEVICE_ID = os.getenv("SIM_DEVICE_ID", "gps-demo-01")
VEHICLE_ID = os.getenv("SIM_VEHICLE_ID", "unit-demo-01")
ROUTE_ID = os.getenv("SIM_ROUTE_ID", "route-l2")
API_BASE_URL = os.getenv("DEV_API_BASE_URL", "http://api:5000").rstrip("/")
POSTGRES_URL = os.getenv("POSTGRES_URL", "")
SPEED_MPS = float(os.getenv("SIM_SPEED_MPS", "8.0"))
INTERVAL_SECONDS = float(os.getenv("SIM_INTERVAL_SECONDS", "2.0"))
START_PROGRESS_M = float(os.getenv("SIM_START_PROGRESS_M", "1200"))


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6_371_000 * 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h))


def bearing_deg(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlon = lon2 - lon1
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def load_route_coordinates() -> list[tuple[float, float]]:
    data = json.loads(ROUTE_PATH.read_text(encoding="utf-8"))
    features = [
        feature
        for feature in data.get("features", [])
        if feature.get("geometry", {}).get("type") == "LineString"
    ]
    if len(features) != 1:
        raise RuntimeError("Expected exactly one L2 LineString")
    return [(float(lat), float(lon)) for lon, lat in features[0]["geometry"]["coordinates"]]


class RouteWalker:
    def __init__(self, coordinates: list[tuple[float, float]], start_progress_m: float):
        self.coordinates = coordinates
        self.segment_lengths = [
            haversine_m(coordinates[index], coordinates[index + 1])
            for index in range(len(coordinates) - 1)
        ]
        self.total_length_m = sum(self.segment_lengths)
        self.progress_m = min(max(start_progress_m, 0.0), self.total_length_m)
        self.direction = 1

    def point_at(self, progress_m: float) -> tuple[float, float]:
        remaining = min(max(progress_m, 0.0), self.total_length_m)
        for index, segment_length in enumerate(self.segment_lengths):
            if remaining <= segment_length or index == len(self.segment_lengths) - 1:
                start = self.coordinates[index]
                end = self.coordinates[index + 1]
                ratio = 0.0 if segment_length <= 0 else remaining / segment_length
                return (
                    start[0] + (end[0] - start[0]) * ratio,
                    start[1] + (end[1] - start[1]) * ratio,
                )
            remaining -= segment_length
        return self.coordinates[-1]

    def step(self, distance_m: float) -> tuple[float, float, float]:
        next_progress = self.progress_m + distance_m * self.direction
        if next_progress >= self.total_length_m:
            overflow = next_progress - self.total_length_m
            self.progress_m = max(0.0, self.total_length_m - overflow)
            self.direction = -1
        elif next_progress <= 0.0:
            overflow = -next_progress
            self.progress_m = min(self.total_length_m, overflow)
            self.direction = 1
        else:
            self.progress_m = next_progress

        position = self.point_at(self.progress_m)
        lookahead = min(
            max(self.progress_m + (12.0 * self.direction), 0.0),
            self.total_length_m,
        )
        target = self.point_at(lookahead)
        heading = bearing_deg(position, target) if target != position else 0.0
        return position[0], position[1], heading


def bootstrap_demo(token: str) -> int:
    if not POSTGRES_URL:
        raise RuntimeError("POSTGRES_URL is required")

    with psycopg.connect(POSTGRES_URL) as conn:
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
                (DEVICE_ID, "GPS demo compartido", hash_token(token)),
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
                (VEHICLE_ID, "Unidad demo compartida", ROUTE_ID, DEVICE_ID),
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
                (ROUTE_ID, VEHICLE_ID),
            )
            cur.execute(
                "SELECT COALESCE(MAX(sequence), -1) + 1 FROM telemetry WHERE device_id = %s;",
                (DEVICE_ID,),
            )
            sequence = int(cur.fetchone()[0])
        conn.commit()
    return sequence


def post_telemetry(token: str, sequence: int, lat: float, lon: float, heading: float) -> None:
    payload = {
        "schema_version": 1,
        "device_id": DEVICE_ID,
        "vehicle_id": VEHICLE_ID,
        "seq": sequence,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "position": {
            "lat": lat,
            "lon": lon,
            "speed_mps": SPEED_MPS,
            "accuracy_m": 4.0,
            "heading_deg": heading,
            "satellites": 10,
        },
    }
    request = Request(
        f"{API_BASE_URL}/v1/telemetry",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Device {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=5) as response:
        if response.status != 202:
            raise RuntimeError(f"Unexpected telemetry status: {response.status}")


def main() -> None:
    if SPEED_MPS <= 0 or INTERVAL_SECONDS <= 0:
        raise RuntimeError("SIM_SPEED_MPS and SIM_INTERVAL_SECONDS must be positive")

    token = secrets.token_urlsafe(32)
    sequence = bootstrap_demo(token)
    walker = RouteWalker(load_route_coordinates(), START_PROGRESS_M)
    print(
        f"Zentryx shared demo started: vehicle={VEHICLE_ID} "
        f"speed={SPEED_MPS:.1f}m/s interval={INTERVAL_SECONDS:.1f}s",
        flush=True,
    )

    while True:
        lat, lon, heading = walker.step(SPEED_MPS * INTERVAL_SECONDS)
        try:
            post_telemetry(token, sequence, lat, lon, heading)
            if sequence % 10 == 0:
                print(
                    f"demo seq={sequence} lat={lat:.6f} lon={lon:.6f} heading={heading:.1f}",
                    flush=True,
                )
            sequence += 1
        except (HTTPError, URLError, TimeoutError, RuntimeError) as error:
            print(f"demo telemetry retry after error: {error}", flush=True)
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
