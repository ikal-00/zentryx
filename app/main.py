import json
import logging
import math
from pathlib import Path

import flet as ft
import flet_map as ftm
from components.passenger import AlertBanner, MapControls, PassengerCard, top_bar
from services import VehicleService
from theme import ACCENT, CARD_WIDTH, INK, MUTED, SOFT, WHITE, configure, shadow

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
        (lat, lon) for lon, lat in route_feature["geometry"]["coordinates"]
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
            "Bandera Tultitlán" if raw_name == "Bandera Tultitlan" else raw_name
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
    """Passenger precision: avoid a distracting seconds counter."""
    if seconds is None:
        return "—"
    if seconds < 60:
        return "<1 min"
    return f"{math.ceil(seconds / 60)} min"


def next_arrival(stations, progress_m, direction, speed_mps):
    # Same route projection, 15 m tolerance and distance/speed as the original.
    ordered = stations if direction == 1 else reversed(stations)
    candidates = [
        station
        for station in ordered
        if (station["progress_m"] - progress_m) * direction > 15.0
    ]
    if not candidates:
        return "Terminal del tramo", 0
    target = candidates[0]
    seconds = (
        abs(target["progress_m"] - progress_m) / speed_mps if speed_mps > 0 else None
    )
    return target["name"], seconds


def main(page: ft.Page):
    configure(page)
    _, route_coordinates, route_points, stations = load_geography()
    vehicle_service = VehicleService(route_coordinates=route_coordinates)
    # Existing service is a demo source. Change this only when its real adapter lands.
    demo_source = True
    station_progress = sorted(
        [
            {
                **station,
                "progress_m": vehicle_service.project_point_to_route(
                    station["lat"], station["lon"]
                ),
            }
            for station in stations
        ],
        key=lambda station: station["progress_m"],
    )
    bus_lat, bus_lon = route_coordinates[0]
    map_state = {
        "follow_vehicle": True,
        "latest_lat": bus_lat,
        "latest_lon": bus_lon,
        "snapshot_count": 0,
        "ready": False,
    }
    station_buttons = {}

    def set_following(following):
        map_state["follow_vehicle"] = following
        controls.set_following(following)

    def highlight_station(name=None):
        for station_name, button in station_buttons.items():
            button.bgcolor = ACCENT if station_name == name else WHITE
            button.icon_color = INK

    def close_station(e=None):
        card.select_station()
        highlight_station()
        page.update()

    async def move_camera(lat, lon, zoom=FOLLOW_ZOOM):
        if map_state["ready"]:
            await mapa.move_to(
                destination=ftm.MapLatitudeLongitude(latitude=lat, longitude=lon),
                zoom=zoom,
                animation_duration=ft.Duration(milliseconds=430),
                animation_curve=ft.AnimationCurve.EASE_OUT_CUBIC,
                cancel_ongoing_animations=True,
            )

    async def select_station(station):
        set_following(False)
        card.select_station(station["name"])
        highlight_station(station["name"])
        page.update()
        await move_camera(station["lat"], station["lon"])

    def station_handler(station, from_dialog=False):
        async def handle(e):
            if from_dialog:
                page.pop_dialog()
            await select_station(station)

        return handle

    def show_route(e):
        page.show_dialog(
            ft.AlertDialog(
                title=ft.Text(
                    "Línea 2 · servicio ordinario",
                    color=INK,
                    weight=ft.FontWeight.W_700,
                ),
                bgcolor=WHITE,
                scrollable=True,
                content=ft.Column(
                    tight=True,
                    spacing=8,
                    controls=[
                        ft.Text(
                            "La Quebrada a Las Américas · 43 paradas",
                            size=13,
                            color=MUTED,
                        ),
                        *[
                            ft.TextButton(
                                content=station["name"],
                                icon=ft.Icons.TRIP_ORIGIN_ROUNDED,
                                height=52,
                                on_click=station_handler(station, from_dialog=True),
                                style=ft.ButtonStyle(
                                    color=INK, alignment=ft.Alignment.CENTER_LEFT
                                ),
                            )
                            for station in station_progress
                        ],
                    ],
                ),
                actions=[ft.TextButton("Cerrar", on_click=lambda e: page.pop_dialog())],
            )
        )

    def show_alert(e):
        if alerts.alert:
            page.show_dialog(
                ft.AlertDialog(
                    title=ft.Text("Aviso de servicio"),
                    content=ft.Text(alerts.alert["message"]),
                    scrollable=True,
                    actions=[
                        ft.TextButton("Entendido", on_click=lambda e: page.pop_dialog())
                    ],
                )
            )

    async def center_on_vehicle(e=None):
        set_following(True)
        card.select_station()
        highlight_station()
        page.update()
        await move_camera(map_state["latest_lat"], map_state["latest_lon"])

    async def handle_map_position_change(e):
        if e.has_gesture and map_state["follow_vehicle"]:
            set_following(False)
            page.update()

    def map_ready(e):
        map_state["ready"] = True

    controls = MapControls(center_on_vehicle)
    card = PassengerCard(close_station)
    alerts = AlertBanner(show_alert)
    # Future adapter may supply an active /v1/alerts item via alerts.set_alert().
    # No request, fabricated alert or empty "all clear" state is generated here.
    route_layer = ftm.PolylineLayer(
        polylines=[
            ftm.PolylineMarker(
                coordinates=route_points,
                color=INK,
                stroke_width=6,
                border_color=WHITE,
                border_stroke_width=2,
            )
        ]
    )
    station_markers = []
    for station in stations:
        button = ft.IconButton(
            icon=ft.Icons.TRIP_ORIGIN_ROUNDED,
            icon_color=INK,
            bgcolor=WHITE,
            icon_size=22,
            width=48,
            height=48,
            tooltip=station["name"],
            on_click=station_handler(station),
            style=ft.ButtonStyle(side=ft.BorderSide(2, INK), shape=ft.CircleBorder()),
        )
        station_buttons[station["name"]] = button
        station_markers.append(
            ftm.Marker(
                coordinates=ftm.MapLatitudeLongitude(
                    latitude=station["lat"], longitude=station["lon"]
                ),
                width=48,
                height=48,
                content=ft.Semantics(
                    label=station["name"],
                    button=True,
                    exclude_semantics=True,
                    on_tap=station_handler(station),
                    content=button,
                ),
            )
        )
    bus_heading_icon = ft.Icon(
        ft.Icons.NAVIGATION_ROUNDED,
        size=25,
        color=ACCENT,
        rotate=0.0,
        animate_rotation=ft.Animation(120, ft.AnimationCurve.LINEAR),
    )
    bus_marker = ftm.Marker(
        coordinates=ftm.MapLatitudeLongitude(latitude=bus_lat, longitude=bus_lon),
        width=54,
        height=54,
        content=ft.Container(
            width=48,
            height=48,
            alignment=ft.Alignment.CENTER,
            bgcolor=INK,
            border_radius=24,
            border=ft.Border.all(3, WHITE),
            shadow=shadow(),
            content=bus_heading_icon,
            tooltip="Unidad · dirección de viaje",
        ),
    )
    mapa = ftm.Map(
        expand=True,
        initial_center=bus_marker.coordinates,
        initial_zoom=FOLLOW_ZOOM,
        min_zoom=12,
        max_zoom=19,
        bgcolor=SOFT,
        animation_duration=ft.Duration(milliseconds=380),
        animation_curve=ft.AnimationCurve.EASE_OUT_CUBIC,
        on_init=map_ready,
        on_position_change=handle_map_position_change,
        layers=[
            ftm.TileLayer(
                url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                user_agent_package_name="zentryx/1.0",
            ),
            route_layer,
            ftm.MarkerLayer(markers=station_markers + [bus_marker]),
            ftm.SimpleAttribution(
                text="OpenStreetMap contributors",
                alignment=ft.Alignment.BOTTOM_LEFT,
                text_style=ft.TextStyle(size=10, color=MUTED),
                bgcolor=WHITE,
            ),
        ],
    )
    map_stack = ft.Stack(
        expand=True,
        controls=[
            mapa,
            ft.Container(left=16, top=16, content=controls.badge),
            ft.Container(right=16, bottom=28, content=controls.center_accessible),
        ],
    )
    header = ft.Container(content=top_bar(show_route))
    dock = ft.Container(
        content=ft.Column(
            tight=True, spacing=8, controls=[alerts.control, card.control]
        )
    )
    dock_outer = ft.Container(
        alignment=ft.Alignment.CENTER,
        padding=ft.Padding.only(left=12, right=12, top=10, bottom=12),
        content=dock,
    )
    body = ft.Column(
        expand=True,
        spacing=0,
        controls=[
            ft.Container(alignment=ft.Alignment.CENTER, content=header),
            map_stack,
            dock_outer,
        ],
    )

    def resize(e=None):
        width = page.width or 390
        header.width = min(width, 1000)
        dock.width = min(max(0, width - 24), CARD_WIDTH)
        # The map remains usable in landscape / with enlarged system text.
        # A bounded scroll region is used only for the card on short screens.
        dock.height = 150 if (page.height or 800) < 560 else None
        dock.content.scroll = ft.ScrollMode.AUTO if dock.height else None
        page.update()

    page.on_resize = resize
    page.add(ft.SafeArea(content=body, expand=True))
    resize()

    async def consume_vehicle_data():
        """Consume the unchanged service; update marker and passenger fields."""
        try:
            async for snapshot in vehicle_service.stream():
                map_state["latest_lat"] = snapshot.lat
                map_state["latest_lon"] = snapshot.lon
                map_state["snapshot_count"] += 1
                bus_marker.coordinates = ftm.MapLatitudeLongitude(
                    latitude=snapshot.lat, longitude=snapshot.lon
                )
                bus_heading_icon.rotate = math.radians(snapshot.heading_deg)
                card.update_vehicle(snapshot, demo=demo_source)
                station, seconds = next_arrival(
                    station_progress,
                    snapshot.progress_m,
                    snapshot.direction,
                    snapshot.speed_mps,
                )
                card.station.value = station
                card.eta.value = "Llegando" if seconds == 0 else format_eta(seconds)
                card.eta.size = 18 if seconds == 0 else 24
                if snapshot.status != "online":
                    card.eta.value = "—"
                page.update()
                if (
                    map_state["follow_vehicle"]
                    and map_state["ready"]
                    and map_state["snapshot_count"] % FOLLOW_EVERY_N_SNAPSHOTS == 0
                ):
                    await move_camera(snapshot.lat, snapshot.lon)
        except Exception:
            logging.getLogger(__name__).exception("Vehicle stream stopped")
            card.status.value = "Sin conexión · última ubicación"
            card.eta.value = "—"
            page.update()

    page.run_task(consume_vehicle_data)


if __name__ == "__main__":
    ft.run(main)
