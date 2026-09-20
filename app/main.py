import json
from pathlib import Path

import flet as ft
import flet_map as ftm

from services import VehicleService


# =====================================
# ZENTRYX - TRAMO PILOTO MEXIBÚS L2
# Buenavista -> Bandera -> Bello Horizonte
# =====================================

GEOJSON_PATH = (
    Path(__file__).parent
    / "assets"
    / "mexibus_l2_buenavista_bandera_bello_horizonte.geojson"
)


def load_geography():
    """Carga la ruta y las estaciones desde el GeoJSON del proyecto."""
    with GEOJSON_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    route_feature = next(
        feature
        for feature in data["features"]
        if feature.get("geometry", {}).get("type") == "LineString"
    )

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


def format_eta(seconds):
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

    vehicle_service = VehicleService(route_coordinates=route_coordinates)

    station_by_name = {station["name"]: station for station in stations}
    bandera = station_by_name["Bandera Tultitlán"]

    station_progress = []
    for station in stations:
        station_progress.append(
            {
                **station,
                "progress_m": vehicle_service.project_point_to_route(
                    station["lat"],
                    station["lon"],
                ),
            }
        )

    station_progress.sort(key=lambda station: station["progress_m"])

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
        .get("distance_m_approx", vehicle_service.route_length_m)
        / 1000
    )

    vehicle_text = ft.Text(f"Unidad: {vehicle_service.vehicle_id}")
    latitude_text = ft.Text(f"Latitud: {bus_lat:.7f}")
    longitude_text = ft.Text(f"Longitud: {bus_lon:.7f}")
    next_station_text = ft.Text("Próxima estación: --")
    eta_text = ft.Text("ETA simulada: --")
    saturation_text = ft.Text("Saturación: --")
    status_text = ft.Text("Estado: esperando datos del servicio...")

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
                            vehicle_text,
                            latitude_text,
                            longitude_text,
                            next_station_text,
                            eta_text,
                            saturation_text,
                            status_text,
                        ],
                    ),
                ),
            ],
        )
    )

    def update_next_station(progress_m, direction, speed_mps):
        tolerance_m = 15.0

        if direction == 1:
            candidates = [
                station
                for station in station_progress
                if station["progress_m"] > progress_m + tolerance_m
            ]
        else:
            candidates = [
                station
                for station in reversed(station_progress)
                if station["progress_m"] < progress_m - tolerance_m
            ]

        if not candidates:
            next_station_text.value = "Próxima estación: Terminal del tramo"
            eta_text.value = "ETA simulada: 0 s"
            return

        target = candidates[0]
        remaining_m = abs(target["progress_m"] - progress_m)

        if speed_mps <= 0:
            eta_text.value = "ETA simulada: --"
        else:
            eta_text.value = (
                f"ETA simulada: {format_eta(remaining_m / speed_mps)}"
            )

        next_station_text.value = f"Próxima estación: {target['name']}"

    async def consume_vehicle_data():
        """La interfaz solo consume estados; no controla la simulación."""
        async for snapshot in vehicle_service.stream():
            bus_marker.coordinates = ftm.MapLatitudeLongitude(
                latitude=snapshot.lat,
                longitude=snapshot.lon,
            )

            vehicle_text.value = f"Unidad: {snapshot.vehicle_id}"
            latitude_text.value = f"Latitud: {snapshot.lat:.7f}"
            longitude_text.value = f"Longitud: {snapshot.lon:.7f}"
            saturation_text.value = (
                f"Saturación: {snapshot.occupancy_level}"
            )
            status_text.value = (
                f"Estado: {snapshot.status} | {snapshot.direction_label}"
            )

            update_next_station(
                snapshot.progress_m,
                snapshot.direction,
                snapshot.speed_mps,
            )

            page.update()

    page.run_task(consume_vehicle_data)


if __name__ == "__main__":
    ft.run(main)
