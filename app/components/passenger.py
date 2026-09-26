"""Small reusable views; data and map actions are supplied by views/passenger.py."""

import flet as ft
from ..theme import ACCENT, INK, LINE, MUTED, PAPER, SOFT, WHITE, shadow


def label(value, **kwargs):
    return ft.Text(value, size=11, color=MUTED, **kwargs)


def pill(value, bgcolor=SOFT, color=INK):
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=10, vertical=5),
        bgcolor=bgcolor,
        border_radius=20,
        content=ft.Text(value, size=11, weight=ft.FontWeight.W_600, color=color),
    )


def top_bar(on_route, line_label="L2", network_name="Mexibús"):
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=20, vertical=14),
        bgcolor=PAPER,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Container(
                            width=36,
                            height=36,
                            bgcolor=INK,
                            border_radius=12,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(ft.Icons.NEAR_ME_ROUNDED, color=ACCENT, size=21),
                        ),
                        ft.Text("zentryx", size=26, weight=ft.FontWeight.W_700, color=INK),
                    ],
                ),
                ft.TextButton(
                    content=ft.Row(
                        spacing=6,
                        tight=True,
                        controls=[
                            pill(line_label, ACCENT),
                            ft.Text(network_name, color=INK, size=13),
                            ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN_ROUNDED, color=INK, size=18),
                        ],
                    ),
                    tooltip="Ver estaciones del servicio",
                    on_click=on_route,
                    style=ft.ButtonStyle(padding=8),
                ),
            ],
        ),
    )


class MapControls:
    def __init__(self, on_center):
        self.status = ft.Text("Siguiendo unidad", size=12, color=INK, weight=ft.FontWeight.W_600)
        self.status_icon = ft.Icon(ft.Icons.GPS_FIXED_ROUNDED, size=14, color=INK)
        self.badge = ft.Container(
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            bgcolor=WHITE,
            border_radius=20,
            shadow=shadow(),
            content=ft.Row(tight=True, spacing=7, controls=[self.status_icon, self.status]),
        )
        self.center = ft.IconButton(
            icon=ft.Icons.GPS_FIXED_ROUNDED,
            icon_size=24,
            width=52,
            height=52,
            icon_color=ACCENT,
            bgcolor=INK,
            tooltip="Centrar y seguir la unidad",
            on_click=on_center,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=18)),
        )
        self.center_accessible = ft.Semantics(
            label="Centrar y seguir la unidad",
            button=True,
            exclude_semantics=True,
            on_tap=on_center,
            content=self.center,
        )

    def set_following(self, following):
        self.status.value = "Siguiendo unidad" if following else "Exploración libre"
        self.status_icon.icon = (
            ft.Icons.GPS_FIXED_ROUNDED if following else ft.Icons.PAN_TOOL_ALT_ROUNDED
        )
        self.center.icon = ft.Icons.GPS_FIXED_ROUNDED if following else ft.Icons.MY_LOCATION_ROUNDED
        self.center.bgcolor = INK if following else WHITE
        self.center.icon_color = ACCENT if following else INK
        self.center.tooltip = "Centrar en la unidad" if following else "Volver a seguir la unidad"
        self.center_accessible.label = self.center.tooltip


class PassengerCard:
    def __init__(self, on_close_station, line_label="L2"):
        self.vehicle = ft.Text(
            "Esperando unidad",
            size=18,
            color=INK,
            weight=ft.FontWeight.W_700,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.destination = ft.Text(
            "Esperando dirección",
            size=12,
            color=MUTED,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.station = ft.Text(
            "Esperando ubicación",
            size=19,
            color=INK,
            weight=ft.FontWeight.W_600,
            max_lines=2,
        )
        self.eta = ft.Text("—", size=30, color=INK, weight=ft.FontWeight.W_700)
        self.status = label("Esperando datos")
        self.occupancy = label("", visible=False)
        self.vehicle_view = ft.Column(
            spacing=14,
            tight=True,
            controls=[
                ft.Row(
                    spacing=12,
                    controls=[
                        ft.Container(
                            width=42,
                            height=42,
                            border_radius=14,
                            bgcolor=SOFT,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(ft.Icons.DIRECTIONS_BUS_ROUNDED, color=INK, size=23),
                        ),
                        ft.Column(
                            expand=True,
                            spacing=2,
                            controls=[self.vehicle, self.destination],
                        ),
                    ],
                ),
                ft.Divider(height=1, color=LINE),
                ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    spacing=14,
                    controls=[
                        ft.Column(
                            expand=True,
                            spacing=5,
                            controls=[label("PRÓXIMA ESTACIÓN"), self.station],
                        ),
                        ft.Container(
                            width=94,
                            padding=10,
                            bgcolor=ACCENT,
                            border_radius=16,
                            content=ft.Column(
                                spacing=0,
                                tight=True,
                                controls=[
                                    ft.Text("LLEGADA EST.", size=10, color=INK),
                                    self.eta,
                                ],
                            ),
                        ),
                    ],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[self.status, self.occupancy],
                ),
            ],
        )
        self.selected_name = ft.Text(
            "", size=21, color=INK, weight=ft.FontWeight.W_700, max_lines=2
        )
        self.station_view = ft.Column(
            visible=False,
            tight=True,
            spacing=12,
            controls=[
                ft.Row(
                    controls=[
                        ft.Column(
                            expand=True,
                            spacing=4,
                            controls=[label(f"ESTACIÓN · {line_label}"), self.selected_name],
                        ),
                        ft.Semantics(
                            label="Volver a la unidad",
                            button=True,
                            exclude_semantics=True,
                            on_tap=on_close_station,
                            content=ft.IconButton(
                                icon=ft.Icons.CLOSE_ROUNDED,
                                width=48,
                                height=48,
                                tooltip="Volver a la unidad",
                                on_click=on_close_station,
                                icon_color=INK,
                            ),
                        ),
                    ]
                ),
                ft.Divider(height=1, color=LINE),
                ft.Text("Llegadas aún no disponibles", size=15, color=INK),
                ft.Text(
                    "Aquí podrás consultar las unidades que se acercan a esta estación.",
                    size=13,
                    color=MUTED,
                ),
            ],
        )
        self.control = ft.Container(
            bgcolor=WHITE,
            padding=20,
            border_radius=26,
            border=ft.Border.all(1, LINE),
            shadow=shadow(),
            content=ft.Column(
                tight=True, spacing=0, controls=[self.vehicle_view, self.station_view]
            ),
        )

    def select_station(self, name=None):
        self.selected_name.value = name or ""
        self.station_view.visible = name is not None
        self.vehicle_view.visible = name is None

    def update_vehicle(self, snapshot, demo=False):
        vehicle_id = snapshot.vehicle_id
        self.vehicle.value = (
            "Unidad " + vehicle_id.rsplit("-", 1)[-1]
            if vehicle_id.startswith(("unit-", "demo-unit-"))
            else vehicle_id
        )
        self.destination.value = "Hacia " + snapshot.direction_label.split("→")[-1].strip()
        self.status.value = (
            "Datos de demostración"
            if demo
            else {
                "online": "Unidad conectada",
                "offline": "Sin conexión · última ubicación",
            }.get(snapshot.status, "Estado no disponible")
        )
        occupancy = {
            "low": "Ocupación baja",
            "medium": "Ocupación media",
            "high": "Ocupación alta",
        }
        self.occupancy.value = occupancy.get(snapshot.occupancy_level, "")
        self.occupancy.visible = bool(self.occupancy.value)


class AlertBanner:
    """Passive /v1/alerts view. Hidden until an actual active alert is supplied."""

    def __init__(self, on_click):
        self.message = ft.Text(
            "", size=13, expand=True, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS
        )
        self.icon = ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, size=20)
        self.control = ft.Container(
            visible=False,
            padding=12,
            border_radius=16,
            on_click=on_click,
            content=ft.Row(
                spacing=8,
                controls=[
                    self.icon,
                    self.message,
                    ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, size=20),
                ],
            ),
        )
        self.alert = None

    def set_alert(self, alert=None):
        self.alert = alert if alert and alert.get("active") and alert.get("message") else None
        self.control.visible = self.alert is not None
        if not self.alert:
            return
        self.message.value = self.alert["message"]
        bg, fg = {
            "critical": ("#FCE9E6", "#9E3026"),
            "warning": ("#FFF0D2", "#80520C"),
        }.get(self.alert.get("severity"), (SOFT, INK))
        self.control.bgcolor = bg
        self.message.color = self.icon.color = fg
