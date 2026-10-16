from typing import Callable
import flet as ft

from app.components.driver.panic_button import PanicSecurityModule
from app.config import ACTIVE_SERVICE_ID
from app.models_driver import EmergencyAlertPayload, OperatorSession
from app.services import load_route
from app.services.driver_service import build_emergency_alert
from app.theme import (
    BRAND,
    BRAND_DARK,
    BRAND_SOFT,
    INK,
    LINE,
    MUTED,
    PAPER,
    SOFT,
    SUCCESS,
    WHITE,
    shadow,
)


class DriverDashboardView:
    """
    Vista 3 del Modo Conductor: Consola Operativa y Módulo de Seguridad (Botón de Pánico SOS).
    - Header con botón SOS rojo de alta visibilidad (con fricción intencional de 3s).
    - Resumen de Operador Verificado, Unidad Asignada y Telemetría GPS activa.
    - Módulo de Pánico con Mantener presionado 3 segundos (ProgressRing) y Deslizar para confirmar.
    - Banner persistente no obstructivo confirmando el envío de coordenadas a Central C5.
    """

    def __init__(
        self,
        page: ft.Page,
        session: OperatorSession,
        on_logout: Callable[[], None],
        on_switch_passenger: Callable[[], None],
    ):
        self.page = page
        self.session = session
        self.on_logout = on_logout
        self.on_switch_passenger = on_switch_passenger

        # Default live coordinates on Mexibús Línea 2 corridor (Ecatepec / Las Américas)
        route = load_route(ACTIVE_SERVICE_ID)
        stations = route.stations
        default_station = stations[6] if len(stations) > 6 else stations[0]
        self.current_lat = default_station.lat
        self.current_lon = default_station.lon
        self.current_station_name = default_station.name

        self.panic_module = PanicSecurityModule(
            page=self.page,
            on_trigger_emergency=self._dispatch_emergency_payload,
        )

        self.control = self._build()

    def _dispatch_emergency_payload(self, trigger_method: str) -> EmergencyAlertPayload:
        return build_emergency_alert(
            session=self.session,
            latitude=self.current_lat,
            longitude=self.current_lon,
            station_context=self.current_station_name,
            trigger_method=trigger_method,
        )

    def _build_header(self) -> ft.Container:
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=20, vertical=12),
            bgcolor=INK,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=12,
                        controls=[
                            ft.Container(
                                width=38,
                                height=38,
                                border_radius=10,
                                bgcolor=BRAND,
                                alignment=ft.Alignment.CENTER,
                                content=ft.Icon(ft.Icons.DIRECTIONS_BUS_ROUNDED, color=WHITE, size=20),
                            ),
                            ft.Column(
                                spacing=1,
                                controls=[
                                    ft.Row(
                                        spacing=6,
                                        controls=[
                                            ft.Text(
                                                f"UNIDAD {self.session.unit_plate or 'MEX-1234'}",
                                                size=14,
                                                weight=ft.FontWeight.W_900,
                                                color=WHITE,
                                            ),
                                            ft.Container(
                                                padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                                border_radius=999,
                                                bgcolor="#0F7644",
                                                content=ft.Text(
                                                    "EN TURNO · INE VERIFICADA",
                                                    size=9,
                                                    weight=ft.FontWeight.W_800,
                                                    color=WHITE,
                                                ),
                                            ),
                                        ],
                                    ),
                                    ft.Text(
                                        f"Op. {self.session.operator_name or 'Carlos E. Mendoza'} · Folio #{self.session.folio or '84021'}",
                                        size=11,
                                        color="#9CA3AF",
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            self.panic_module.header_sos_button,
                            ft.OutlinedButton(
                                content=ft.Text("Modo Pasajero", size=11, weight=ft.FontWeight.W_700, color=WHITE),
                                style=ft.ButtonStyle(
                                    side=ft.BorderSide(1, "#374151"),
                                    shape=ft.RoundedRectangleBorder(radius=999),
                                ),
                                on_click=lambda _: self.on_switch_passenger(),
                            ),
                        ],
                    ),
                ],
            ),
        )

    def _build_operator_summary_card(self) -> ft.Container:
        vehicle = self.session.vehicle
        econ = vehicle.economic_number if vehicle else "U-042"
        service = vehicle.service_type if vehicle else "Expreso Articulado BRT"
        route_label = vehicle.route_name if vehicle else "Línea 2 · Las Américas ⇄ La Quebrada"

        return ft.Container(
            padding=20,
            border_radius=20,
            bgcolor=WHITE,
            border=ft.Border.all(1, LINE),
            shadow=shadow(),
            content=ft.Column(
                spacing=14,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text(
                                        "ESTADO OPERATIVO DE UNIDAD",
                                        size=11,
                                        weight=ft.FontWeight.W_800,
                                        color=BRAND,
                                    ),
                                    ft.Text(
                                        route_label,
                                        size=16,
                                        weight=ft.FontWeight.W_800,
                                        color=INK,
                                    ),
                                ],
                            ),
                            ft.Container(
                                padding=ft.Padding.symmetric(horizontal=10, vertical=5),
                                border_radius=999,
                                bgcolor="#DCFCE7",
                                content=ft.Text(
                                    "TELEMETRÍA C5 ACTIVA",
                                    size=10,
                                    weight=ft.FontWeight.W_800,
                                    color=SUCCESS,
                                ),
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=10,
                        wrap=True,
                        controls=[
                            self._metric_pill("No. Económico", econ, ft.Icons.NUMBERS_ROUNDED),
                            self._metric_pill("Matrícula", self.session.unit_plate or "MEX-1234", ft.Icons.BADGE_OUTLINED),
                            self._metric_pill("Servicio", service, ft.Icons.SPEED_ROUNDED),
                            self._metric_pill(
                                "Coordenadas GPS",
                                f"{self.current_lat:.4f}, {self.current_lon:.4f}",
                                ft.Icons.MY_LOCATION_ROUNDED,
                            ),
                        ],
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                f"✓ Identidad INE validada ({self.session.ine.verified_at or 'Turno actual'}) · Próxima estación: {self.current_station_name}",
                                size=12,
                                color=MUTED,
                            ),
                            ft.TextButton(
                                content=ft.Text(
                                    "Finalizar Turno",
                                    size=12,
                                    weight=ft.FontWeight.W_700,
                                    color=BRAND,
                                ),
                                on_click=lambda _: self.on_logout(),
                            ),
                        ],
                    ),
                ],
            ),
        )

    def _metric_pill(self, label: str, value: str, icon_name) -> ft.Container:
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            border_radius=12,
            bgcolor=PAPER,
            border=ft.Border.all(1, LINE),
            content=ft.Row(
                spacing=8,
                tight=True,
                controls=[
                    ft.Icon(icon_name, size=16, color=BRAND),
                    ft.Column(
                        spacing=1,
                        tight=True,
                        controls=[
                            ft.Text(label, size=10, color=MUTED, weight=ft.FontWeight.W_600),
                            ft.Text(value, size=12, color=INK, weight=ft.FontWeight.W_800),
                        ],
                    ),
                ],
            ),
        )

    def _build(self) -> ft.Container:
        return ft.Container(
            expand=True,
            bgcolor=PAPER,
            content=ft.Column(
                expand=True,
                spacing=0,
                controls=[
                    self._build_header(),
                    ft.Container(
                        expand=True,
                        padding=20,
                        alignment=ft.Alignment.TOP_CENTER,
                        content=ft.Container(
                            width=520,
                            content=ft.Column(
                                scroll=ft.ScrollMode.AUTO,
                                spacing=16,
                                controls=[
                                    self.panic_module.persistent_alert_banner,
                                    self._build_operator_summary_card(),
                                    self.panic_module.panel_control,
                                ],
                            ),
                        ),
                    ),
                ],
            ),
        )
