"""Immutable route and vehicle data shared by adapters and presentation."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StationDefinition:
    station_id: str
    name: str
    stop_order: int
    lat: float
    lon: float


@dataclass(frozen=True)
class RouteDefinition:
    route_id: str
    line_id: str
    line_label: str
    network_name: str
    service_id: str
    service_name: str
    origin_name: str
    destination_name: str
    forward_label: str
    reverse_label: str
    coordinates: tuple[tuple[float, float], ...]
    stations: tuple[StationDefinition, ...]
    route_source_path: Path | None
    stations_source_path: Path | None

    @property
    def station_count(self) -> int:
        return len(self.stations)


@dataclass(frozen=True)
class VehicleSnapshot:
    vehicle_id: str
    route_id: str
    status: str
    lat: float
    lon: float
    speed_mps: float
    occupancy_level: str
    direction: int
    direction_label: str
    progress_m: float
    route_length_m: float
    heading_deg: float


@dataclass(frozen=True)
class ApiVehicleSnapshot(VehicleSnapshot):
    next_station_name: str | None = None
    eta_seconds: float | None = None
    distance_remaining_m: float | None = None
    navigation_from_api: bool = True
    position_known: bool = True
