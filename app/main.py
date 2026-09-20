import asyncio
import json
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

# Qué tan suave se ve la simulación.
INTERPOLATION_STEPS = 20
UPDATE_INTERVAL_SECONDS = 0.15


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
        yield (
            start_lat + (end_lat - start_lat) * progress,
            start_lon + (end_lon - start_lon) * progress,
        )


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
        .get("distance_m_approx", 0)
        / 1000
    )

    latitude_text = ft.Text(f"Latitud: {bus_lat:.7f}")
    longitude_text = ft.Text(f"Longitud: {bus_lon:.7f}")
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
                            ft.Text("Llegada: --"),
                            ft.Text("Saturación: --"),
                            status_text,
                        ],
                    ),
                ),
            ],
        )
    )

    async def animate_bus():
        """Mueve continuamente la unidad sobre la polilínea real."""
        direction = 1

        while True:
            if direction == 1:
                points = route_coordinates
                status = "Simulación: Buenavista → Bello Horizonte"
            else:
                points = list(reversed(route_coordinates))
                status = "Simulación: Bello Horizonte → Buenavista"

            status_text.value = f"Estado: {status}"
            page.update()

            for index in range(len(points) - 1):
                start = points[index]
                end = points[index + 1]

                for lat, lon in interpolate(
                    start,
                    end,
                    INTERPOLATION_STEPS,
                ):
                    bus_marker.coordinates = ftm.MapLatitudeLongitude(
                        latitude=lat,
                        longitude=lon,
                    )
                    latitude_text.value = f"Latitud: {lat:.7f}"
                    longitude_text.value = f"Longitud: {lon:.7f}"

                    page.update()
                    await asyncio.sleep(UPDATE_INTERVAL_SECONDS)

            # Asegura que el bus llegue exactamente al último punto.
            final_lat, final_lon = points[-1]
            bus_marker.coordinates = ftm.MapLatitudeLongitude(
                latitude=final_lat,
                longitude=final_lon,
            )
            latitude_text.value = f"Latitud: {final_lat:.7f}"
            longitude_text.value = f"Longitud: {final_lon:.7f}"
            page.update()

            await asyncio.sleep(1)
            direction *= -1

    page.run_task(animate_bus)


if __name__ == "__main__":
    ft.run(main)
