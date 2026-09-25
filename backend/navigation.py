"""Server-side route projection used for production navigation/ETA fields."""

from __future__ import annotations

import bisect
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class NavigationResult:
    direction: int | None
    direction_source: str | None
    progress_m: float | None
    route_length_m: float
    next_station_id: str | None
    next_station_name: str | None
    distance_remaining_m: float | None
    eta_seconds: float | None
    eta_speed_mps: float | None


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

    @staticmethod
    def bearing_deg(a, b):
        lat1, lon1 = map(math.radians, a)
        lat2, lon2 = map(math.radians, b)
        delta_lon = lon2 - lon1
        x = math.sin(delta_lon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon)
        return (math.degrees(math.atan2(x, y)) + 360.0) % 360.0

    @staticmethod
    def angular_difference(a, b):
        return abs((float(a) - float(b) + 180.0) % 360.0 - 180.0)

    def _build_distances(self):
        cumulative = [0.0]
        for index in range(len(self.coordinates) - 1):
            cumulative.append(
                cumulative[-1]
                + self.haversine_m(self.coordinates[index], self.coordinates[index + 1])
            )
        return cumulative

    def coordinate_at_progress(self, progress_m):
        progress_m = max(0.0, min(self.route_length_m, float(progress_m)))
        if progress_m <= 0:
            return self.coordinates[0]
        if progress_m >= self.route_length_m:
            return self.coordinates[-1]
        index = bisect.bisect_right(self.cumulative_distances, progress_m) - 1
        index = max(0, min(index, len(self.coordinates) - 2))
        start = self.cumulative_distances[index]
        end = self.cumulative_distances[index + 1]
        length = end - start
        if length <= 0:
            return self.coordinates[index]
        fraction = (progress_m - start) / length
        lat1, lon1 = self.coordinates[index]
        lat2, lon2 = self.coordinates[index + 1]
        return (
            lat1 + (lat2 - lat1) * fraction,
            lon1 + (lon2 - lon1) * fraction,
        )

    def forward_bearing_at_progress(self, progress_m):
        before = max(0.0, float(progress_m) - 8.0)
        after = min(self.route_length_m, float(progress_m) + 8.0)
        if after == before:
            return None
        return self.bearing_deg(
            self.coordinate_at_progress(before),
            self.coordinate_at_progress(after),
        )

    def project_point(self, lat, lon):
        lat = float(lat)
        lon = float(lon)
        reference_lat = math.radians(lat)
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
                segment_length = self.cumulative_distances[index + 1] - self.cumulative_distances[index]
                best_progress_m = self.cumulative_distances[index] + fraction * segment_length

        return best_progress_m

    def _infer_direction(self, progress_m, history, heading_deg):
        # Use a window of older GPS points, not only one noisy sample.
        for sample in history or []:
            lat = sample.get("lat")
            lon = sample.get("lon")
            if lat is None or lon is None:
                continue
            previous_progress = self.project_point(lat, lon)
            delta = progress_m - previous_progress
            if abs(delta) >= 4.0:
                return (1 if delta > 0 else -1), "history"

        # When stopped, a valid heading can preserve a stable route direction.
        if heading_deg is not None:
            forward_bearing = self.forward_bearing_at_progress(progress_m)
            if forward_bearing is not None:
                if self.angular_difference(heading_deg, forward_bearing) <= 90.0:
                    return 1, "heading"
                return -1, "heading"
        return None, None

    @staticmethod
    def _eta_speed(speed_mps, smoothed_speed_mps, default_speed_mps):
        for value in (smoothed_speed_mps, speed_mps):
            if value is not None and float(value) >= 1.0:
                return float(value)
        if default_speed_mps is not None and float(default_speed_mps) > 0:
            return float(default_speed_mps)
        return None

    def navigation(
        self,
        *,
        lat,
        lon,
        history=None,
        heading_deg=None,
        speed_mps=None,
        smoothed_speed_mps=None,
        default_speed_mps=6.0,
    ):
        progress_m = self.project_point(lat, lon)
        direction, direction_source = self._infer_direction(progress_m, history, heading_deg)
        eta_speed_mps = self._eta_speed(speed_mps, smoothed_speed_mps, default_speed_mps)

        if direction is None:
            return NavigationResult(
                direction=None,
                direction_source=None,
                progress_m=progress_m,
                route_length_m=self.route_length_m,
                next_station_id=None,
                next_station_name=None,
                distance_remaining_m=None,
                eta_seconds=None,
                eta_speed_mps=eta_speed_mps,
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
                direction_source=direction_source,
                progress_m=progress_m,
                route_length_m=self.route_length_m,
                next_station_id=None,
                next_station_name=None,
                distance_remaining_m=0.0,
                eta_seconds=0.0,
                eta_speed_mps=eta_speed_mps,
            )

        target = candidates[0]
        distance_remaining_m = abs(target["progress_m"] - progress_m)
        eta_seconds = (
            distance_remaining_m / eta_speed_mps
            if eta_speed_mps is not None and eta_speed_mps > 0
            else None
        )
        return NavigationResult(
            direction=direction,
            direction_source=direction_source,
            progress_m=progress_m,
            route_length_m=self.route_length_m,
            next_station_id=target["station_id"],
            next_station_name=target["name"],
            distance_remaining_m=distance_remaining_m,
            eta_seconds=eta_seconds,
            eta_speed_mps=eta_speed_mps,
        )
