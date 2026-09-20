import asyncio
import json
import math
from pathlib import Path

import flet as ft
import flet_map as ftm


# =====================================
# ZENTRYX - TRAMO PILOTO MEXIBÚS L2
# Buenavista -> Bandera -> Bello Horizonte
# =====================================

GEOJSON_PATH = (
    Path(__file__).parent
    / "assets"
    / "mexibus_l2_buenavista_bandera_bello_horizonte.geojson"
)

# Configuración visual de la simulación.
INTERPOLATION_STEPS = 20
UPDATE_INTERVAL_SECONDS = 0.15

# Velocidad usada únicamente para calcular la ETA simulada.
SIMULATED_SPEED_MPS = 8.0


def load_geography():
    """Carga la ruta y las estaciones desde el GeoJSON del proyecto."""
    with GEOJSON_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    route_feature = next(
        feature
        for feature in data["features"]
        if feature.get("geometry", {}).get("type") == "LineString"
    )

    # GeoJSON usa [longitud, latitud]. Para trabajar en la app lo
    # convertimos a pares (latitud, longitud).
    route_coordinates = [
        (lat, lon)
        for lon, lat in route_feature["geometry"]["coordinates"]
    ]

    route_points = [
        ftm.MapLatitudeLongitude(latitude=lat, longitude=lon)
        for lat, lon in route_coordinates
    ]

    stations = []
    for feature in data["features"]:
        if feature.get("geometry", {}).get("type") != "Point":
            continue

        lon, lat = feature["geometry"]["coordinates"]
        raw_name = feature.get("properties", {}).get("name", "Estación")

        display_name = (
            "Bandera Tultitlán"
            if raw_name == "Bandera Tultitlan"
            else raw_name
        )

        stations.append(
            {
                "name": display_name,
                "lat": lat,
                "lon": lon,
            }
        )

    return route_feature, route_coordinates, route_points, stations


def interpolate(start, end, steps):
    """Genera posiciones intermedias entre dos puntos de la ruta."""
    start_lat, start_lon = start
    end_lat, end_lon = end

    for step in range(steps):
        progress = step / steps
        yield progress, (
            start_lat + (end_lat - start_lat) * progress,
            start_lon + (end_lon - start_lon) * progress,
        )


def haversine_m(point_a, point_b):
    """Distancia aproximada en metros entre dos coordenadas WGS84."""
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


def build_route_distances(route_coordinates):
    """Crea la distancia acumulada de cada punto de la polilínea."""
    cumulative = [0.0]

    for index in range(len(route_coordinates) - 1):
        segment_distance = haversine_m(
            route_coordinates[index],
            route_coordinates[index + 1],
        )
        cumulative.append(cumulative[-1] + segment_distance)

    return cumulative


def project_station_to_route(station, route_coordinates, cumulative):
    """
    Proyecta una estación sobre el segmento más cercano de la ruta y
    devuelve su distancia acumulada desde Buenavista.
    """
    station_lat = station["lat"]
    station_lon = station["lon"]

    # Para este tramo pequeño basta una proyección local en metros.
    reference_lat = math.radians(station_lat)
    meters_per_lat_degree = 111_320.0
    meters_per_lon_degree = 111_320.0 * math.cos(reference_lat)

    best_distance_squared = float("inf")
    best_progress_m = 0.0

    for index in range(len(route_coordinates) - 1):
        start_lat, start_lon = route_coordinates[index]
        end_lat, end_lon = route_coordinates[index + 1]

        ax = (start_lon - station_lon) * meters_per_lon_degree
        ay = (start_lat - station_lat) * meters_per_lat_degree
        bx = (end_lon - station_lon) * meters_per_lon_degree
        by = (end_lat - station_lat) * meters_per_lat_degree

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
            segment_distance = cumulative[index + 1] - cumulative[index]
            best_progress_m = cumulative[index] + fraction * segment_distance

    return best_progress_m


def format_eta(seconds):
    """Convierte segundos a un texto corto de ETA."""
    seconds = max(0, int(round(seconds)))

    if seconds < 60:
        return f"{seconds} s"

    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes} min {remaining_seconds:02d} s"


def main(page: ft.Page):
    page.title = "Zentryx"
    page.padding = 0

    (
        route_feature,
        route_coordinates,
        route_points,
        stations,
    ) = load_geography()

    station_by_name = {station["name"]: station for station in stations}
    bandera = station_by_name["Bandera Tultitlán"]

    cumulative_distances = build_route_distances(route_coordinates)
    route_length_m = cumulative_distances[-1]

    station_progress = []
    for station in stations:
        progress_m = project_station_to_route(
            station,
            route_coordinates,
            cumulative_distances,
        )
        station_progress.append(
            {
                **station,
                "progress_m": progress_m,
            }
        )

    station_progress.sort(key=lambda station: station["progress_m"])

    # La simulación comienza al inicio del tramo real: Buenavista.
    bus_lat, bus_lon = route_coordinates[0]

    route_layer = ftm.PolylineLayer(
        polylines=[
            ftm.PolylineMarker(
                coordinates=route_points,
                color=ft.Colors.BLUE,
                stroke_width=7,
                border_color=ft.Colors.WHITE,
                border_stroke_width=2,
            )
        ]
    )

    station_markers = []
    for station in stations:
        is_bandera = station["name"] == "Bandera Tultitlán"

        station_markers.append(
            ftm.Marker(
                coordinates=ftm.MapLatitudeLongitude(
                    latitude=station["lat"],
                    longitude=station["lon"],
                ),
                width=45,
                height=45,
                content=ft.Icon(
                    ft.Icons.LOCATION_ON,
                    size=38 if is_bandera else 32,
                    color=(
                        ft.Colors.RED
                        if is_bandera
                        else ft.Colors.BLUE_GREY
                    ),
                ),
            )
        )

    bus_marker = ftm.Marker(
        coordinates=ftm.MapLatitudeLongitude(
            latitude=bus_lat,
            longitude=bus_lon,
        ),
        width=50,
        height=50,
        content=ft.Icon(
            ft.Icons.DIRECTIONS_BUS,
            size=40,
            color=ft.Colors.BLACK,
        ),
    )

    mapa = ftm.Map(
        expand=True,
        initial_center=ftm.MapLatitudeLongitude(
            latitude=bandera["lat"],
            longitude=bandera["lon"],
        ),
        initial_zoom=16,
        min_zoom=12,
        max_zoom=19,
        layers=[
            ftm.TileLayer(
                url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                user_agent_package_name="zentryx/1.0",
            ),
            route_layer,
            ftm.MarkerLayer(markers=station_markers + [bus_marker]),
            ftm.SimpleAttribution(text="OpenStreetMap contributors"),
        ],
    )

    distance_km = (
        route_feature.get("properties", {})
        .get("distance_m_approx", route_length_m)
        / 1000
    )

    latitude_text = ft.Text(f"Latitud: {bus_lat:.7f}")
    longitude_text = ft.Text(f"Longitud: {bus_lon:.7f}")
    next_station_text = ft.Text("Próxima estación: --")
    eta_text = ft.Text("ETA simulada: --")
    status_text = ft.Text("Estado: Iniciando simulación...")

    page.add(
        ft.Column(
            expand=True,
            spacing=0,
            controls=[
                ft.Container(
                    padding=15,
                    content=ft.Text(
                        "ZENTRYX",
                        size=26,
                        weight=ft.FontWeight.BOLD,
                    ),
                ),
                ft.Container(
                    expand=True,
                    content=mapa,
                ),
                ft.Container(
                    padding=15,
                    content=ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text(
                                "Mexibús Línea 2 - Tramo piloto",
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                "Buenavista → Bandera Tultitlán → Bello Horizonte"
                            ),
                            ft.Text(
                                f"Distancia aproximada: {distance_km:.2f} km"
                            ),
                            ft.Text("Unidad: demo-unit-01"),
                            latitude_text,
                            longitude_text,
                            next_station_text,
                            eta_text,
                            ft.Text("Saturación: --"),
                            status_text,
                        ],
                    ),
                ),
            ],
        )
    )

    def update_next_station(current_progress_m, direction):
        """Actualiza próxima estación y ETA según el sentido del bus."""
        tolerance_m = 15.0

        if direction == 1:
            candidates = [
                station
                for station in station_progress
                if station["progress_m"] > current_progress_m + tolerance_m
            ]
        else:
            candidates = [
                station
                for station in reversed(station_progress)
                if station["progress_m"] < current_progress_m - tolerance_m
            ]

        if not candidates:
            next_station_text.value = "Próxima estación: Terminal del tramo"
            eta_text.value = "ETA simulada: 0 s"
            return

        target = candidates[0]
        remaining_m = abs(target["progress_m"] - current_progress_m)
        eta_seconds = remaining_m / SIMULATED_SPEED_MPS

        next_station_text.value = f"Próxima estación: {target['name']}"
        eta_text.value = f"ETA simulada: {format_eta(eta_seconds)}"

    async def animate_bus():
        """Mueve continuamente la unidad sobre la polilínea real."""
        direction = 1

        while True:
            if direction == 1:
                segment_indexes = range(len(route_coordinates) - 1)
                status = "Simulación: Buenavista → Bello Horizonte"
            else:
                segment_indexes = range(len(route_coordinates) - 1, 0, -1)
                status = "Simulación: Bello Horizonte → Buenavista"

            status_text.value = f"Estado: {status}"
            page.update()

            for index in segment_indexes:
                if direction == 1:
                    start = route_coordinates[index]
                    end = route_coordinates[index + 1]
                    segment_start_progress = cumulative_distances[index]
                    segment_distance = (
                        cumulative_distances[index + 1]
                        - cumulative_distances[index]
                    )
                else:
                    start = route_coordinates[index]
                    end = route_coordinates[index - 1]
                    segment_start_progress = cumulative_distances[index]
                    segment_distance = (
                        cumulative_distances[index]
                        - cumulative_distances[index - 1]
                    )

                for fraction, (lat, lon) in interpolate(
                    start,
                    end,
                    INTERPOLATION_STEPS,
                ):
                    if direction == 1:
                        current_progress_m = (
                            segment_start_progress
                            + fraction * segment_distance
                        )
                    else:
                        current_progress_m = (
                            segment_start_progress
                            - fraction * segment_distance
                        )

                    bus_marker.coordinates = ftm.MapLatitudeLongitude(
                        latitude=lat,
                        longitude=lon,
                    )
                    latitude_text.value = f"Latitud: {lat:.7f}"
                    longitude_text.value = f"Longitud: {lon:.7f}"
                    update_next_station(current_progress_m, direction)

                    page.update()
                    await asyncio.sleep(UPDATE_INTERVAL_SECONDS)

            if direction == 1:
                final_lat, final_lon = route_coordinates[-1]
                final_progress_m = route_length_m
            else:
                final_lat, final_lon = route_coordinates[0]
                final_progress_m = 0.0

            bus_marker.coordinates = ftm.MapLatitudeLongitude(
                latitude=final_lat,
                longitude=final_lon,
            )
            latitude_text.value = f"Latitud: {final_lat:.7f}"
            longitude_text.value = f"Longitud: {final_lon:.7f}"
            update_next_station(final_progress_m, direction)
            page.update()

            await asyncio.sleep(1)
            direction *= -1

    page.run_task(animate_bus)


if __name__ == "__main__":
    ft.run(main)
