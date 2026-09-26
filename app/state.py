"""Per-page camera state, independent of Flet controls."""

from dataclasses import dataclass
from .config import FOLLOW_CAMERA_INTERVAL_SECONDS, FOLLOW_MIN_DISTANCE_M
from .services.vehicle_service import VehicleService


@dataclass
class MapState:
    latest_lat: float
    latest_lon: float
    position_known: bool
    last_follow_lat: float
    last_follow_lon: float
    follow_vehicle: bool = True
    ready: bool = False
    last_follow_at: float = 0.0

    def should_follow(self, lat, lon, now):
        if not self.follow_vehicle or not self.ready or not self.position_known:
            return False
        if now - self.last_follow_at < FOLLOW_CAMERA_INTERVAL_SECONDS:
            return False
        distance = VehicleService.haversine_m(
            (self.last_follow_lat, self.last_follow_lon), (lat, lon)
        )
        if distance < FOLLOW_MIN_DISTANCE_M:
            return False
        self.last_follow_at = now
        self.last_follow_lat, self.last_follow_lon = lat, lon
        return True
