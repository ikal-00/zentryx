import json
import math
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

FOLLOW_ZOOM = 16.5
FOLLOW_EVERY_N_SNAPSHOTS = 6


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

    # Estado local de la cámara. Si el usuario mueve el mapa manualmente,
    # el seguimiento se desactiva hasta que pulse el botón de centrar.
    map_state = {
        "follow_vehicle": True,
        "latest_lat": bus_lat,
        "latest_lon": bus_lon,
        "snapshot_count": 0,
    }

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

    # Marcador de aviso de prueba. Después vendrá de /v1/alerts.
    alert_marker = ftm.Marker(
        coordinates=ftm.MapLatitudeLongitude(
            latitude=bandera["lat"] + 0.00035,
            longitude=bandera["lon"],
        ),
        width=118,
        height=38,
        content=ft.Container(
            padding=ft.Padding.symmetric(horizontal=9, vertical=5),
            bgcolor=ft.Colors.AMBER_100,
            border_radius=18,
            content=ft.Row(
                spacing=5,
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Icon(
                        ft.Icons.WARNING_AMBER_ROUNDED,
                        size=17,
                        color=ft.Colors.AMBER_900,
                    ),
                    ft.Text(
                        "Aviso demo",
                        size=11,
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
            ),
        ),
    )

    # Icono direccional tipo navegación. El círculo queda estable y la
    # flecha rota con el heading de la unidad.
    bus_heading_icon = ft.Icon(
        ft.Icons.NAVIGATION_ROUNDED,
        size=24,
        color=ft.Colors.WHITE,
        rotate=0.0,
        animate_rotation=ft.Animation(120, ft.AnimationCurve.LINEAR),
    )

    bus_marker = ftm.Marker(
        coordinates=ftm.MapLatitudeLongitude(
            latitude=bus_lat,
            longitude=bus_lon,
        ),
        width=46,
        height=46,
        content=ft.Container(
            width=42,
            height=42,
            alignment=ft.Alignment.CENTER,
            bgcolor=ft.Colors.BLUE_700,
            border_radius=21,
            border=ft.Border.all(3, ft.Colors.WHITE),
            content=bus_heading_icon,
        ),
    )

    follow_status = ft.Text(
        "Siguiendo unidad",
        size=11,
        color=ft.Colors.BLUE_GREY_700,
    )

    async def handle_map_position_change(e):
        if e.has_gesture and map_state["follow_vehicle"]:
            map_state["follow_vehicle"] = False
            follow_status.value = "Mapa libre · pulsa centrar para seguir"
            center_button.icon = ft.Icons.MY_LOCATION
            page.update()

    mapa = ftm.Map(
        expand=True,
        initial_center=ftm.MapLatitudeLongitude(
            latitude=bandera["lat"],
            longitude=bandera["lon"],
        ),
        initial_zoom=16,
        min_zoom=12,
        max_zoom=19,
        animation_duration=ft.Duration(milliseconds=380),
        animation_curve=ft.AnimationCurve.EASE_OUT_CUBIC,
        on_position_change=handle_map_position_change,
        layers=[
            ftm.TileLayer(
                url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                user_agent_package_name="zentryx/1.0",
            ),
            route_layer,
            ftm.MarkerLayer(
                markers=station_markers + [alert_marker, bus_marker]
            ),
            ftm.SimpleAttribution(text="OpenStreetMap contributors"),
        ],
    )

    async def center_on_vehicle(e=None):
        map_state["follow_vehicle"] = True
        follow_status.value = "Siguiendo unidad"
        center_button.icon = ft.Icons.GPS_FIXED

        await mapa.move_to(
            destination=ftm.MapLatitudeLongitude(
                latitude=map_state["latest_lat"],
                longitude=map_state["latest_lon"],
            ),
            zoom=FOLLOW_ZOOM,
            animation_duration=ft.Duration(milliseconds=450),
            animation_curve=ft.AnimationCurve.EASE_OUT_CUBIC,
            cancel_ongoing_animations=True,
        )
        page.update()

    center_button = ft.IconButton(
        icon=ft.Icons.GPS_FIXED,
        tooltip="Centrar en la unidad",
        icon_color=ft.Colors.BLUE_700,
        bgcolor=ft.Colors.WHITE,
        on_click=center_on_vehicle,
    )

    map_stack = ft.Stack(
        expand=True,
        controls=[
            mapa,
            ft.Container(
                right=16,
                bottom=18,
                content=center_button,
            ),
            ft.Container(
                left=14,
                top=14,
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                bgcolor=ft.Colors.with_opacity(0.92, ft.Colors.WHITE),
                border_radius=16,
                content=follow_status,
            ),
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
    speed_text = ft.Text("Velocidad: --")
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
                    content=map_stack,
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
                            speed_text,
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
        """Consume estados y mantiene el mapa suave y centrable."""
        async for snapshot in vehicle_service.stream():
            map_state["latest_lat"] = snapshot.lat
            map_state["latest_lon"] = snapshot.lon
            map_state["snapshot_count"] += 1

            bus_marker.coordinates = ftm.MapLatitudeLongitude(
                latitude=snapshot.lat,
                longitude=snapshot.lon,
            )

            # Flet rota en radianes. NAVIGATION apunta hacia arriba, por lo
            # que el heading 0° coincide naturalmente con norte.
            bus_heading_icon.rotate = math.radians(snapshot.heading_deg)

            vehicle_text.value = f"Unidad: {snapshot.vehicle_id}"
            latitude_text.value = f"Latitud: {snapshot.lat:.7f}"
            longitude_text.value = f"Longitud: {snapshot.lon:.7f}"
            speed_text.value = f"Velocidad: {snapshot.speed_mps * 3.6:.1f} km/h"
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

            # No movemos la cámara en cada frame: así la transición se siente
            # estable y no pelea contra las animaciones del mapa.
            if (
                map_state["follow_vehicle"]
                and map_state["snapshot_count"] % FOLLOW_EVERY_N_SNAPSHOTS == 0
            ):
                await mapa.move_to(
                    destination=ftm.MapLatitudeLongitude(
                        latitude=snapshot.lat,
                        longitude=snapshot.lon,
                    ),
                    zoom=FOLLOW_ZOOM,
                    animation_duration=ft.Duration(milliseconds=430),
                    animation_curve=ft.AnimationCurve.LINEAR,
                    cancel_ongoing_animations=True,
                )

    page.run_task(consume_vehicle_data)


if __name__ == "__main__":
    ft.run(main)
