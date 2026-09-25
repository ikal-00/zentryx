"""Server-side route projection used for production navigation/ETA fields."""

from __future__ import annotations

import bisect
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class NavigationResult:
    direction: int | None
    progress_m: float | None
    route_length_m: float
    next_station_id: str | None
    next_station_name: str | None
    distance_remaining_m: float | None
    eta_seconds: float | None


class RouteNavigator:
    def __init__(self, coordinates, stations):
        if len(coordinates) < 2:
            raise ValueError("route requires at least two coordinates")
        self.coordinates = [(float(lat), float(lon)) for lat, lon in coordinates]
        self.cumulative_distances = self._build_distances()
        self.route_length_m = self.cumulative_distances[-1]
        self.stations = []
        for station in stations:
            item = dict(station)
            item["progress_m"] = self.project_point(item["lat"], item["lon"])
            self.stations.append(item)
        self.stations.sort(key=lambda station: station["stop_order"])

    @staticmethod
    def haversine_m(a, b):
        lat1, lon1 = a
        lat2, lon2 = b
        radius_m = 6_371_000.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        value = (
            math.sin(delta_phi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        )
        return 2 * radius_m * math.atan2(math.sqrt(value), math.sqrt(1 - value))

    def _build_distances(self):
        cumulative = [0.0]
        for index in range(len(self.coordinates) - 1):
            cumulative.append(
                cumulative[-1]
                + self.haversine_m(self.coordinates[index], self.coordinates[index + 1])
            )
        return cumulative

    def project_point(self, lat, lon):
        reference_lat = math.radians(float(lat))
        meters_per_lat_degree = 111_320.0
        meters_per_lon_degree = 111_320.0 * math.cos(reference_lat)
        best_distance_squared = float("inf")
        best_progress_m = 0.0

        for index in range(len(self.coordinates) - 1):
            start_lat, start_lon = self.coordinates[index]
            end_lat, end_lon = self.coordinates[index + 1]
            ax = (start_lon - lon) * meters_per_lon_degree
            ay = (start_lat - lat) * meters_per_lat_degree
            bx = (end_lon - lon) * meters_per_lon_degree
            by = (end_lat - lat) * meters_per_lat_degree
            dx = bx - ax
            dy = by - ay
            length_squared = dx * dx + dy * dy
            if length_squared == 0:
                fraction = 0.0
            else:
                fraction = -(ax * dx + ay * dy) / length_squared
                fraction = max(0.0, min(1.0, fraction))

            nearest_x = ax + fraction * dx
            nearest_y = ay + fraction * dy
            distance_squared = nearest_x**2 + nearest_y**2
            if distance_squared < best_distance_squared:
                best_distance_squared = distance_squared
                segment_length = (
                    self.cumulative_distances[index + 1]
                    - self.cumulative_distances[index]
                )
                best_progress_m = self.cumulative_distances[index] + fraction * segment_length

        return best_progress_m

    def navigation(self, *, lat, lon, previous_lat, previous_lon, speed_mps):
        progress_m = self.project_point(lat, lon)
        direction = None
        if previous_lat is not None and previous_lon is not None:
            previous_progress = self.project_point(previous_lat, previous_lon)
            delta = progress_m - previous_progress
            if abs(delta) >= 1.5:
                direction = 1 if delta > 0 else -1

        if direction is None:
            return NavigationResult(
                direction=None,
                progress_m=progress_m,
                route_length_m=self.route_length_m,
                next_station_id=None,
                next_station_name=None,
                distance_remaining_m=None,
                eta_seconds=None,
            )

        ordered = self.stations if direction == 1 else reversed(self.stations)
        candidates = [
            station
            for station in ordered
            if (station["progress_m"] - progress_m) * direction > 15.0
        ]
        if not candidates:
            return NavigationResult(
                direction=direction,
                progress_m=progress_m,
                route_length_m=self.route_length_m,
                next_station_id=None,
                next_station_name=None,
                distance_remaining_m=0.0,
                eta_seconds=0.0,
            )

        target = candidates[0]
        distance_remaining_m = abs(target["progress_m"] - progress_m)
        eta_seconds = (
            distance_remaining_m / float(speed_mps)
            if speed_mps is not None and float(speed_mps) > 0
            else None
        )
        return NavigationResult(
            direction=direction,
            progress_m=progress_m,
            route_length_m=self.route_length_m,
            next_station_id=target["station_id"],
            next_station_name=target["name"],
            distance_remaining_m=distance_remaining_m,
            eta_seconds=eta_seconds,
        )
