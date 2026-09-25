"""REST adapter that exposes the backend using the existing vehicle stream shape."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, replace
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .vehicle_service import VehicleService, VehicleSnapshot


@dataclass(frozen=True)
class ApiVehicleSnapshot(VehicleSnapshot):
    next_station_name: str | None = None
    eta_seconds: float | None = None
    distance_remaining_m: float | None = None
    navigation_from_api: bool = False


class ApiVehicleService(VehicleService):
    """Poll `/v1/vehicles/{id}` while preserving map geometry helpers."""

    def __init__(
        self,
        route_coordinates,
        *,
        base_url: str,
        vehicle_id: str,
        route_id: str,
        forward_direction_label: str,
        reverse_direction_label: str,
        poll_interval_seconds: float = 1.0,
        request_timeout_seconds: float = 4.0,
    ):
        super().__init__(
            route_coordinates=route_coordinates,
            vehicle_id=vehicle_id,
            route_id=route_id,
            speed_mps=0.0,
            update_interval_seconds=poll_interval_seconds,
            forward_direction_label=forward_direction_label,
            reverse_direction_label=reverse_direction_label,
        )
        self.base_url = base_url.rstrip("/")
        self.poll_interval_seconds = poll_interval_seconds
        self.request_timeout_seconds = request_timeout_seconds

    def _fetch_vehicle(self):
        request = Request(
            f"{self.base_url}/v1/vehicles/{self.vehicle_id}",
            headers={"Accept": "application/json"},
        )
        with urlopen(request, timeout=self.request_timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    def _snapshot_from_payload(self, payload):
        position = payload.get("position")
        if not isinstance(position, dict):
            raise ValueError("vehicle has no known position")

        navigation = payload.get("navigation") or {}
        direction_name = navigation.get("direction")
        direction = 1 if direction_name == "forward" else -1 if direction_name == "reverse" else 1
        direction_label = navigation.get("direction_label") or (
            self.forward_direction_label if direction == 1 else self.reverse_direction_label
        )
        next_station = navigation.get("next_station") or {}

        return ApiVehicleSnapshot(
            vehicle_id=str(payload.get("vehicle_id", self.vehicle_id)),
            route_id=str(payload.get("route_id") or self.route_id),
            status=str(payload.get("status") or "unknown"),
            lat=float(position["lat"]),
            lon=float(position["lon"]),
            speed_mps=float(payload.get("speed_mps") or 0.0),
            occupancy_level=str(payload.get("occupancy_level") or "unknown"),
            direction=direction,
            direction_label=direction_label,
            progress_m=float(navigation.get("progress_m") or 0.0),
            route_length_m=float(navigation.get("route_length_m") or self.route_length_m),
            heading_deg=float(payload.get("heading_deg") or 0.0),
            next_station_name=next_station.get("name"),
            eta_seconds=(
                float(navigation["eta_seconds"])
                if navigation.get("eta_seconds") is not None
                else None
            ),
            distance_remaining_m=(
                float(navigation["distance_remaining_m"])
                if navigation.get("distance_remaining_m") is not None
                else None
            ),
            navigation_from_api=bool(navigation),
        )

    async def stream(self):
        last_snapshot = None
        while True:
            try:
                payload = await asyncio.to_thread(self._fetch_vehicle)
                last_snapshot = self._snapshot_from_payload(payload)
                yield last_snapshot
            except (HTTPError, URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError):
                if last_snapshot is not None:
                    yield replace(last_snapshot, status="offline", eta_seconds=None)
            await asyncio.sleep(self.poll_interval_seconds)
