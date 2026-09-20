import asyncio
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


class VehicleService:
    """Fuente de datos de vehículos para la app.

    Hoy genera datos simulados sobre la ruta. Más adelante esta clase podrá
    sustituir la simulación por llamadas a GET /v1/vehicles/{vehicle_id}
    sin obligar a reescribir la interfaz del mapa.
    """

    def __init__(
        self,
        route_coordinates: list[tuple[float, float]],
        vehicle_id: str = "demo-unit-01",
        route_id: str = "route-l2",
        speed_mps: float = 8.0,
        interpolation_steps: int = 20,
        update_interval_seconds: float = 0.15,
    ):
        if len(route_coordinates) < 2:
            raise ValueError("La ruta necesita al menos dos coordenadas")

        self.route_coordinates = route_coordinates
        self.vehicle_id = vehicle_id
        self.route_id = route_id
        self.speed_mps = speed_mps
        self.interpolation_steps = interpolation_steps
        self.update_interval_seconds = update_interval_seconds

        self.cumulative_distances = self._build_route_distances()
        self.route_length_m = self.cumulative_distances[-1]

    @staticmethod
    def haversine_m(point_a: tuple[float, float], point_b: tuple[float, float]) -> float:
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

        return 2 * radius_m * math.atan2(math.sqrt(value), math.sqrt(1 - value))

    def _build_route_distances(self) -> list[float]:
        cumulative = [0.0]

        for index in range(len(self.route_coordinates) - 1):
            segment_distance = self.haversine_m(
                self.route_coordinates[index],
                self.route_coordinates[index + 1],
            )
            cumulative.append(cumulative[-1] + segment_distance)

        return cumulative

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

    def _interpolate(self, start, end):
        start_lat, start_lon = start
        end_lat, end_lon = end

        for step in range(self.interpolation_steps):
            fraction = step / self.interpolation_steps
            yield fraction, (
                start_lat + (end_lat - start_lat) * fraction,
                start_lon + (end_lon - start_lon) * fraction,
            )

    async def stream(self) -> AsyncIterator[VehicleSnapshot]:
        """Emite estados simulados del vehículo de forma continua."""
        direction = 1

        while True:
            if direction == 1:
                segment_indexes = range(len(self.route_coordinates) - 1)
                direction_label = "Buenavista → Bello Horizonte"
            else:
                segment_indexes = range(len(self.route_coordinates) - 1, 0, -1)
                direction_label = "Bello Horizonte → Buenavista"

            for index in segment_indexes:
                if direction == 1:
                    start = self.route_coordinates[index]
                    end = self.route_coordinates[index + 1]
                    segment_start_progress = self.cumulative_distances[index]
                    segment_distance = (
                        self.cumulative_distances[index + 1]
                        - self.cumulative_distances[index]
                    )
                else:
                    start = self.route_coordinates[index]
                    end = self.route_coordinates[index - 1]
                    segment_start_progress = self.cumulative_distances[index]
                    segment_distance = (
                        self.cumulative_distances[index]
                        - self.cumulative_distances[index - 1]
                    )

                for fraction, (lat, lon) in self._interpolate(start, end):
                    if direction == 1:
                        progress_m = segment_start_progress + fraction * segment_distance
                    else:
                        progress_m = segment_start_progress - fraction * segment_distance

                    yield VehicleSnapshot(
                        vehicle_id=self.vehicle_id,
                        route_id=self.route_id,
                        status="online",
                        lat=lat,
                        lon=lon,
                        speed_mps=self.speed_mps,
                        occupancy_level="unknown",
                        direction=direction,
                        direction_label=direction_label,
                        progress_m=progress_m,
                        route_length_m=self.route_length_m,
                    )

                    await asyncio.sleep(self.update_interval_seconds)

            final_lat, final_lon = (
                self.route_coordinates[-1]
                if direction == 1
                else self.route_coordinates[0]
            )
            final_progress_m = self.route_length_m if direction == 1 else 0.0

            yield VehicleSnapshot(
                vehicle_id=self.vehicle_id,
                route_id=self.route_id,
                status="online",
                lat=final_lat,
                lon=final_lon,
                speed_mps=0.0,
                occupancy_level="unknown",
                direction=direction,
                direction_label=direction_label,
                progress_m=final_progress_m,
                route_length_m=self.route_length_m,
            )

            await asyncio.sleep(1)
            direction *= -1
