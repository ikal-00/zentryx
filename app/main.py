import logging
import math
import os
import time

import flet as ft
import flet_map as ftm
from components.passenger import AlertBanner, MapControls, PassengerCard, top_bar
from services import (
    ApiAlertService,
    ApiVehicleService,
    VehicleService,
    load_route,
    load_route_from_api,
)
from theme import ACCENT, CARD_WIDTH, INK, MUTED, SOFT, WHITE, configure, shadow


ACTIVE_SERVICE_ID = "l2-ordinary"
FOLLOW_ZOOM = 16.5
FOLLOW_CAMERA_INTERVAL_SECONDS = 0.85
FOLLOW_MIN_DISTANCE_M = 4.0
FOLLOW_ANIMATION_MS = 420


def load_geography(route=None):
    """Carga una variante y conserva el formato que usa el frontend."""
    route = route or load_route(ACTIVE_SERVICE_ID)
    route_coordinates = list(route.coordinates)
    route_points = [
        ftm.MapLatitudeLongitude(latitude=lat, longitude=lon)
        for lat, lon in route_coordinates
    ]
    stations = [
        {
            "station_id": station.station_id,
            "name": station.name,
            "stop_order": station.stop_order,
            "lat": station.lat,
            "lon": station.lon,
        }
        for station in route.stations
    ]
    return route, route_coordinates, route_points, stations


def format_eta(seconds):
    if seconds is None:
        return "—"
    if seconds < 60:
        return "<1 min"
    return f"{math.ceil(seconds / 60)} min"


def next_arrival(stations, progress_m, direction, speed_mps):
    """Fallback usado únicamente por la fuente demo local."""
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
        abs(target["progress_m"] - progress_m) / speed_mps
        if speed_mps > 0
        else None
    )
    return target["name"], seconds


def unwrap_heading_radians(previous_rotation, heading_deg):
    previous_rotation = float(previous_rotation or 0.0)
    target = math.radians(heading_deg) % math.tau
    previous_normalized = previous_rotation % math.tau
    delta = (target - previous_normalized + math.pi) % math.tau - math.pi
    return previous_rotation + delta


def main(page: ft.Page):
    configure(page)

    api_base_url = os.getenv("ZENTRYX_API_BASE_URL", "").strip()
    service_id = os.getenv("ZENTRYX_SERVICE_ID", ACTIVE_SERVICE_ID).strip()
    route_from_api = False
    route = None
    if api_base_url:
        try:
            route = load_route_from_api(
                api_base_url,
                service_id=service_id,
            )
            route_from_api = True
        except Exception:
            logging.getLogger(__name__).exception(
                "Could not load route from API; using local route asset"
            )

    if route is None:
        route = load_route(service_id if service_id in (ACTIVE_SERVICE_ID,) else ACTIVE_SERVICE_ID)

    route, route_coordinates, route_points, stations = load_geography(route)

    if api_base_url:
        vehicle_id = os.getenv("ZENTRYX_VEHICLE_ID", "unit-01")
        vehicle_service = ApiVehicleService(
            route_coordinates=route_coordinates,
            base_url=api_base_url,
            vehicle_id=vehicle_id,
            route_id=route.route_id,
            forward_direction_label=route.forward_label,
            reverse_direction_label=route.reverse_label,
        )
        alert_service = ApiAlertService(
            base_url=api_base_url,
            route_id=route.route_id,
            vehicle_id=vehicle_id,
        )
        demo_source = False
    else:
        vehicle_service = VehicleService(
            route_coordinates=route_coordinates,
            route_id=route.route_id,
            forward_direction_label=route.forward_label,
            reverse_direction_label=route.reverse_label,
        )
        alert_service = None
        demo_source = True

    station_progress = [
        {
            **station,
            "progress_m": vehicle_service.project_point_to_route(
                station["lat"],
                station["lon"],
            ),
        }
        for station in stations
    ]

    bus_lat, bus_lon = route_coordinates[0]
    map_state = {
        "follow_vehicle": True,
        "latest_lat": bus_lat,
        "latest_lon": bus_lon,
        "position_known": demo_source,
        "ready": False,
        "last_follow_at": 0.0,
        "last_follow_lat": bus_lat,
        "last_follow_lon": bus_lon,
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
                animation_duration=ft.Duration(milliseconds=FOLLOW_ANIMATION_MS),
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
        source_label = "API" if route_from_api else "datos locales"
        page.show_dialog(
            ft.AlertDialog(
                title=ft.Text(
                    f"{route.line_label} · {route.service_name}",
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
                            f"{route.origin_name} a {route.destination_name} · "
                            f"{route.station_count} estaciones · {source_label}",
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
                                    color=INK,
                                    alignment=ft.Alignment.CENTER_LEFT,
                                ),
                            )
                            for station in station_progress
                        ],
                    ],
                ),
                actions=[
                    ft.TextButton("Cerrar", on_click=lambda event: page.pop_dialog())
                ],
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
                        ft.TextButton(
                            "Entendido",
                            on_click=lambda event: page.pop_dialog(),
                        )
                    ],
                )
            )

    async def center_on_vehicle(e=None):
        set_following(True)
        card.select_station()
        highlight_station()
        page.update()
        if map_state["position_known"]:
            await move_camera(map_state["latest_lat"], map_state["latest_lon"])
            map_state["last_follow_at"] = time.monotonic()
            map_state["last_follow_lat"] = map_state["latest_lat"]
            map_state["last_follow_lon"] = map_state["latest_lon"]

    async def handle_map_position_change(e):
        if e.has_gesture and map_state["follow_vehicle"]:
            set_following(False)
            page.update()

    def map_ready(e):
        map_state["ready"] = True

    controls = MapControls(center_on_vehicle)
    card = PassengerCard(close_station, line_label=route.line_label)
    alerts = AlertBanner(show_alert)

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
            style=ft.ButtonStyle(
                side=ft.BorderSide(2, INK),
                shape=ft.CircleBorder(),
            ),
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
    bus_container = ft.Container(
        width=48,
        height=48,
        alignment=ft.Alignment.CENTER,
        bgcolor=INK,
        border_radius=24,
        border=ft.Border.all(3, WHITE),
        shadow=shadow(),
        content=bus_heading_icon,
        tooltip="Unidad · dirección de viaje",
        visible=demo_source,
    )
    bus_marker = ftm.Marker(
        coordinates=ftm.MapLatitudeLongitude(latitude=bus_lat, longitude=bus_lon),
        width=54,
        height=54,
        content=bus_container,
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
                text="© OpenStreetMap contributors",
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

    header = ft.Container(
        content=top_bar(
            show_route,
            line_label=route.line_label,
            network_name=route.network_name,
        )
    )
    dock = ft.Container(
        content=ft.Column(
            tight=True,
            spacing=8,
            controls=[alerts.control, card.control],
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
        dock.height = 150 if (page.height or 800) < 560 else None
        dock.content.scroll = ft.ScrollMode.AUTO if dock.height else None
        page.update()

    page.on_resize = resize
    page.add(ft.SafeArea(content=body, expand=True))
    resize()

    def should_follow_camera(snapshot):
        if (
            not map_state["follow_vehicle"]
            or not map_state["ready"]
            or not map_state["position_known"]
        ):
            return False
        now = time.monotonic()
        if now - map_state["last_follow_at"] < FOLLOW_CAMERA_INTERVAL_SECONDS:
            return False
        distance = VehicleService.haversine_m(
            (map_state["last_follow_lat"], map_state["last_follow_lon"]),
            (snapshot.lat, snapshot.lon),
        )
        if distance < FOLLOW_MIN_DISTANCE_M:
            return False
        map_state["last_follow_at"] = now
        map_state["last_follow_lat"] = snapshot.lat
        map_state["last_follow_lon"] = snapshot.lon
        return True

    async def consume_vehicle_data():
        try:
            async for snapshot in vehicle_service.stream():
                position_known = getattr(snapshot, "position_known", True)
                map_state["position_known"] = position_known
                bus_container.visible = position_known

                if position_known:
                    map_state["latest_lat"] = snapshot.lat
                    map_state["latest_lon"] = snapshot.lon
                    bus_marker.coordinates = ftm.MapLatitudeLongitude(
                        latitude=snapshot.lat,
                        longitude=snapshot.lon,
                    )
                    bus_heading_icon.rotate = unwrap_heading_radians(
                        bus_heading_icon.rotate,
                        snapshot.heading_deg,
                    )

                card.update_vehicle(snapshot, demo=demo_source)

                if getattr(snapshot, "navigation_from_api", False):
                    seconds = getattr(snapshot, "eta_seconds", None)
                    station = getattr(snapshot, "next_station_name", None)
                    if not position_known:
                        station = "Esperando ubicación"
                    elif station is None:
                        station = (
                            "Terminal del tramo"
                            if seconds == 0
                            else "Calculando próxima estación"
                        )
                else:
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
                if position_known and should_follow_camera(snapshot):
                    await move_camera(snapshot.lat, snapshot.lon)

        except Exception:
            logging.getLogger(__name__).exception("Vehicle stream stopped")
            card.status.value = "Sin conexión · última ubicación"
            card.eta.value = "—"
            page.update()

    async def consume_alerts():
        async for alert in alert_service.stream():
            alerts.set_alert(alert)
            page.update()

    page.run_task(consume_vehicle_data)
    if alert_service is not None:
        page.run_task(consume_alerts)


if __name__ == "__main__":
    ft.run(main)
