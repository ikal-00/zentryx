"""Shared development simulator for the Zentryx API.

This module is intentionally opt-in through the Docker Compose ``demo`` profile.
It creates a dedicated demo device/vehicle and an active test alert, then sends
fresh telemetry through the real HTTP API so route projection, direction, ETA,
offline handling and alerts can be tested end to end.
"""

from __future__ import annotations

import json
import os
import secrets
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


from .repositories.demo import bootstrap_demo as provision_demo


from .config import ROUTE_PATH
from .services.simulation import RouteWalker


DEVICE_ID = os.getenv("SIM_DEVICE_ID", "gps-demo-01")
VEHICLE_ID = os.getenv("SIM_VEHICLE_ID", "unit-demo-01")
ROUTE_ID = os.getenv("SIM_ROUTE_ID", "route-l2")
API_BASE_URL = os.getenv("DEV_API_BASE_URL", "http://api:5000").rstrip("/")
POSTGRES_URL = os.getenv("POSTGRES_URL", "")
SPEED_MPS = float(os.getenv("SIM_SPEED_MPS", "8.0"))
INTERVAL_SECONDS = float(os.getenv("SIM_INTERVAL_SECONDS", "2.0"))
START_PROGRESS_M = float(os.getenv("SIM_START_PROGRESS_M", "1200"))


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


def bootstrap_demo(token: str) -> int:
    return provision_demo(POSTGRES_URL, DEVICE_ID, VEHICLE_ID, ROUTE_ID, token)


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
