import asyncio
import bisect
import math
from dataclasses import dataclass
from typing import AsyncIterator


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


class VehicleService:
    """Fuente de datos de vehículos para la app.

    Hoy genera datos simulados sobre la ruta. El movimiento se calcula por
    distancia recorrida (m/s), no por una cantidad fija de pasos por segmento,
    para que la velocidad visual sea constante incluso cuando los puntos del
    GeoJSON están separados por distancias diferentes.

    La identidad de la ruta y sus etiquetas de dirección se inyectan desde la
    definición de servicio, así esta clase no depende de Línea 2.
    """

    def __init__(
        self,
        route_coordinates: list[tuple[float, float]],
        vehicle_id: str = "demo-unit-01",
        route_id: str = "route-demo",
        speed_mps: float = 8.0,
        update_interval_seconds: float = 0.08,
        terminal_pause_seconds: float = 1.0,
        forward_direction_label: str = "Ida",
        reverse_direction_label: str = "Vuelta",
    ):
        if len(route_coordinates) < 2:
            raise ValueError("La ruta necesita al menos dos coordenadas")

        self.route_coordinates = route_coordinates
        self.vehicle_id = vehicle_id
        self.route_id = route_id
        self.speed_mps = speed_mps
        self.update_interval_seconds = update_interval_seconds
        self.terminal_pause_seconds = terminal_pause_seconds
        self.forward_direction_label = forward_direction_label
        self.reverse_direction_label = reverse_direction_label

        self.cumulative_distances = self._build_route_distances()
        self.route_length_m = self.cumulative_distances[-1]

    @staticmethod
    def haversine_m(
        point_a: tuple[float, float],
        point_b: tuple[float, float],
    ) -> float:
        lat1, lon1 = point_a
        lat2, lon2 = point_b

        radius_m = 6_371_000
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        value = (
            math.sin(delta_phi / 2) ** 2
            + math.cos(phi1)
            * math.cos(phi2)
            * math.sin(delta_lambda / 2) ** 2
        )

        return 2 * radius_m * math.atan2(
            math.sqrt(value),
            math.sqrt(1 - value),
        )

    @staticmethod
    def bearing_deg(
        point_a: tuple[float, float],
        point_b: tuple[float, float],
    ) -> float:
        """Rumbo de A hacia B en grados: 0=N, 90=E, 180=S, 270=O."""
        lat1, lon1 = map(math.radians, point_a)
        lat2, lon2 = map(math.radians, point_b)

        delta_lon = lon2 - lon1
        x = math.sin(delta_lon) * math.cos(lat2)
        y = (
            math.cos(lat1) * math.sin(lat2)
            - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon)
        )

        return (math.degrees(math.atan2(x, y)) + 360.0) % 360.0

    def _build_route_distances(self) -> list[float]:
        cumulative = [0.0]

        for index in range(len(self.route_coordinates) - 1):
            segment_distance = self.haversine_m(
                self.route_coordinates[index],
                self.route_coordinates[index + 1],
            )
            cumulative.append(cumulative[-1] + segment_distance)

        return cumulative

    def coordinate_at_progress(self, progress_m: float) -> tuple[float, float]:
        """Devuelve una coordenada interpolada a una distancia dada de la ruta."""
        progress_m = max(0.0, min(self.route_length_m, progress_m))

        if progress_m <= 0:
            return self.route_coordinates[0]
        if progress_m >= self.route_length_m:
            return self.route_coordinates[-1]

        index = bisect.bisect_right(
            self.cumulative_distances,
            progress_m,
        ) - 1
        index = max(0, min(index, len(self.route_coordinates) - 2))

        start_distance = self.cumulative_distances[index]
        end_distance = self.cumulative_distances[index + 1]
        segment_distance = end_distance - start_distance

        if segment_distance <= 0:
            return self.route_coordinates[index]

        fraction = (progress_m - start_distance) / segment_distance
        start_lat, start_lon = self.route_coordinates[index]
        end_lat, end_lon = self.route_coordinates[index + 1]

        return (
            start_lat + (end_lat - start_lat) * fraction,
            start_lon + (end_lon - start_lon) * fraction,
        )

    def heading_at_progress(self, progress_m: float, direction: int) -> float:
        """Calcula el rumbo usando dos puntos cercanos sobre la propia ruta."""
        lookahead_m = 8.0

        if direction == 1:
            start_progress = progress_m
            end_progress = min(self.route_length_m, progress_m + lookahead_m)
            if end_progress == start_progress:
                start_progress = max(0.0, progress_m - lookahead_m)
        else:
            start_progress = progress_m
            end_progress = max(0.0, progress_m - lookahead_m)
            if end_progress == start_progress:
                start_progress = min(
                    self.route_length_m,
                    progress_m + lookahead_m,
                )

        return self.bearing_deg(
            self.coordinate_at_progress(start_progress),
            self.coordinate_at_progress(end_progress),
        )

    def project_point_to_route(self, lat: float, lon: float) -> float:
        """Devuelve la distancia acumulada del punto más cercano sobre la ruta."""
        reference_lat = math.radians(lat)
        meters_per_lat_degree = 111_320.0
        meters_per_lon_degree = 111_320.0 * math.cos(reference_lat)

        best_distance_squared = float("inf")
        best_progress_m = 0.0

        for index in range(len(self.route_coordinates) - 1):
            start_lat, start_lon = self.route_coordinates[index]
            end_lat, end_lon = self.route_coordinates[index + 1]

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
                segment_distance = (
                    self.cumulative_distances[index + 1]
                    - self.cumulative_distances[index]
                )
                best_progress_m = (
                    self.cumulative_distances[index]
                    + fraction * segment_distance
                )

        return best_progress_m

    def _snapshot(self, progress_m: float, direction: int, speed_mps: float):
        lat, lon = self.coordinate_at_progress(progress_m)
        direction_label = (
            self.forward_direction_label
            if direction == 1
            else self.reverse_direction_label
        )

        return VehicleSnapshot(
            vehicle_id=self.vehicle_id,
            route_id=self.route_id,
            status="online",
            lat=lat,
            lon=lon,
            speed_mps=speed_mps,
            occupancy_level="unknown",
            direction=direction,
            direction_label=direction_label,
            progress_m=progress_m,
            route_length_m=self.route_length_m,
            heading_deg=self.heading_at_progress(progress_m, direction),
        )

    async def stream(self) -> AsyncIterator[VehicleSnapshot]:
        """Emite posiciones a velocidad constante sobre la distancia de la ruta."""
        direction = 1
        progress_m = 0.0

        while True:
            yield self._snapshot(
                progress_m=progress_m,
                direction=direction,
                speed_mps=self.speed_mps,
            )

            await asyncio.sleep(self.update_interval_seconds)

            distance_step = self.speed_mps * self.update_interval_seconds
            progress_m += distance_step * direction

            reached_terminal = (
                direction == 1 and progress_m >= self.route_length_m
            ) or (
                direction == -1 and progress_m <= 0.0
            )

            if reached_terminal:
                progress_m = (
                    self.route_length_m if direction == 1 else 0.0
                )

                yield self._snapshot(
                    progress_m=progress_m,
                    direction=direction,
                    speed_mps=0.0,
                )

                await asyncio.sleep(self.terminal_pause_seconds)
                direction *= -1
