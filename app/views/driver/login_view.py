from typing import Callable
import flet as ft

from app.components.driver.auth_inputs import OperatorAuthCard
from app.components.driver.qr_scanner_modal import build_qr_scanner_dialog
from app.models_driver import OperatorSession
from app.services.driver_service import apply_credentials_to_session
from app.theme import (
    BRAND,
    BRAND_DARK,
    BRAND_SOFT,
    INK,
    LINE,
    MUTED,
    PAPER,
    SOFT,
    WHITE,
    shadow,
)


class DriverLoginView:
    """
    Vista 1 del Modo Conductor: Pantalla de Autenticación de Operador (Login).
    """

    def __init__(
        self,
        page: ft.Page,
        session: OperatorSession,
        on_authenticated: Callable[[], None],
        on_switch_passenger: Callable[[], None],
    ):
        self.page = page
        self.session = session
        self.on_authenticated = on_authenticated
        self.on_switch_passenger = on_switch_passenger

        self.auth_card = OperatorAuthCard(
            session=self.session,
            on_credentials_change=self._handle_credentials_change,
            on_open_qr=self._handle_open_qr,
            on_submit_login=self._handle_submit,
        )

        self.control = self._build()

    def _handle_credentials_change(self, folio: str, plate: str) -> None:
        apply_credentials_to_session(self.session, folio, plate, auth_method="manual")
        self.auth_card.sync_from_session()
        self.page.update()

    def _handle_open_qr(self) -> None:
        dialog = build_qr_scanner_dialog(
            page=self.page,
            on_qr_verified=self._on_qr_verified,
        )
        self.page.show_dialog(dialog)

    def _on_qr_verified(self, folio: str, plate: str, token: str) -> None:
        apply_credentials_to_session(self.session, folio, plate, auth_method="qr")
        self.auth_card.sync_from_session()
        self.page.update()

    def _handle_submit(self) -> None:
        if self.session.is_valid_assignment:
            self.session.mark_authenticated(self.session.auth_method)
            self.on_authenticated()

    def _build_header(self) -> ft.Container:
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=20, vertical=14),
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
                                content=ft.Text(
                                    "Z",
                                    size=18,
                                    weight=ft.FontWeight.W_900,
                                    color=WHITE,
                                ),
                            ),
                            ft.Column(
                                spacing=1,
                                controls=[
                                    ft.Row(
                                        spacing=6,
                                        controls=[
                                            ft.Text(
                                                "ZENTRYX",
                                                size=15,
                                                weight=ft.FontWeight.W_900,
                                                color=WHITE,
                                            ),
                                            ft.Container(
                                                padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                                border_radius=999,
                                                bgcolor=BRAND,
                                                content=ft.Text(
                                                    "MODO CONDUCTOR",
                                                    size=9,
                                                    weight=ft.FontWeight.W_800,
                                                    color=WHITE,
                                                ),
                                            ),
                                        ],
                                    ),
                                    ft.Text(
                                        "Plataforma Operativa Mexibús · Estándar Tier-1",
                                        size=11,
                                        color="#9CA3AF",
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.OutlinedButton(
                        content=ft.Row(
                            spacing=6,
                            tight=True,
                            controls=[
                                ft.Icon(ft.Icons.DIRECTIONS_TRANSIT_ROUNDED, size=16, color=WHITE),
                                ft.Text(
                                    "Modo Pasajero",
                                    size=12,
                                    weight=ft.FontWeight.W_700,
                                    color=WHITE,
                                ),
                            ],
                        ),
                        style=ft.ButtonStyle(
                            side=ft.BorderSide(1, "#374151"),
                            shape=ft.RoundedRectangleBorder(radius=999),
                        ),
                        on_click=lambda _: self.on_switch_passenger(),
                    ),
                ],
            ),
        )

    def _build_stepper(self) -> ft.Container:
        return ft.Container(
            width=480,
            padding=ft.Padding.symmetric(horizontal=16, vertical=10),
            border_radius=14,
            bgcolor=WHITE,
            border=ft.Border.all(1, LINE),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=6,
                        controls=[
                            ft.Container(
                                width=22,
                                height=22,
                                border_radius=999,
                                bgcolor=BRAND,
                                alignment=ft.Alignment.CENTER,
                                content=ft.Text("1", size=11, weight=ft.FontWeight.W_800, color=WHITE),
                            ),
                            ft.Text("1. Login Operador", size=12, weight=ft.FontWeight.W_800, color=INK),
                        ],
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, size=16, color=MUTED),
                    ft.Row(
                        spacing=6,
                        controls=[
                            ft.Container(
                                width=22,
                                height=22,
                                border_radius=999,
                                bgcolor=SOFT,
                                alignment=ft.Alignment.CENTER,
                                content=ft.Text("2", size=11, weight=ft.FontWeight.W_700, color=MUTED),
                            ),
                            ft.Text("2. Captura INE", size=12, weight=ft.FontWeight.W_600, color=MUTED),
                        ],
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, size=16, color=MUTED),
                    ft.Row(
                        spacing=6,
                        controls=[
                            ft.Container(
                                width=22,
                                height=22,
                                border_radius=999,
                                bgcolor=SOFT,
                                alignment=ft.Alignment.CENTER,
                                content=ft.Text("3", size=11, weight=ft.FontWeight.W_700, color=MUTED),
                            ),
                            ft.Text("3. Consola y SOS", size=12, weight=ft.FontWeight.W_600, color=MUTED),
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
                        content=ft.Column(
                            scroll=ft.ScrollMode.AUTO,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=16,
                            controls=[
                                self._build_stepper(),
                                self.auth_card.control,
                            ],
                        ),
                    ),
                ],
            ),
        )
