from typing import Callable, Optional
import flet as ft

from app.models_driver import OperatorSession
from app.theme import (
    BRAND,
    BRAND_DARK,
    BRAND_SOFT,
    BRAND_STRONG,
    INK,
    LINE,
    MUTED,
    PAPER,
    SOFT,
    SUCCESS,
    WARNING,
    WHITE,
    shadow,
)


class OperatorAuthCard:
    """
    Componente de Autenticación de Operador:
    - Input numérico grande y legible para Folio Único de Operador / No. de Empleado.
    - Input alfanumérico para Matrícula de la Unidad (Placas, ej. MEX-1234).
    - Indicador visual animado ('Operador Vigente y Asignado') usando animate y animate_opacity.
    - Botón secundario prominente 'Escanear Código QR'.
    """

    def __init__(
        self,
        session: OperatorSession,
        on_credentials_change: Callable[[str, str], None],
        on_open_qr: Callable[[], None],
        on_submit_login: Callable[[], None],
    ):
        self.session = session
        self.on_credentials_change = on_credentials_change
        self.on_open_qr = on_open_qr
        self.on_submit_login = on_submit_login

        self.folio_input = ft.TextField(
            value=session.folio,
            label="Folio Único de Operador / No. de Empleado",
            hint_text="Ej. 84021",
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=22,
            height=68,
            border_radius=14,
            border_color=LINE,
            focused_border_color=BRAND,
            focused_border_width=2,
            bgcolor=PAPER,
            color=INK,
            cursor_color=BRAND,
            prefix_icon=ft.Icons.BADGE_OUTLINED,
            content_padding=ft.Padding.symmetric(horizontal=18, vertical=16),
            text_style=ft.TextStyle(
                size=22,
                weight=ft.FontWeight.W_800,
                color=INK,
            ),
            label_style=ft.TextStyle(
                size=13,
                weight=ft.FontWeight.W_600,
                color=MUTED,
            ),
            on_change=self._handle_change,
            on_submit=lambda _: self._try_submit(),
        )

        self.plate_input = ft.TextField(
            value=session.unit_plate,
            label="Matrícula de la Unidad (Placas)",
            hint_text="Ej. MEX-1234",
            capitalization=ft.TextCapitalization.CHARACTERS,
            text_size=19,
            height=64,
            border_radius=14,
            border_color=LINE,
            focused_border_color=BRAND,
            focused_border_width=2,
            bgcolor=PAPER,
            color=INK,
            cursor_color=BRAND,
            prefix_icon=ft.Icons.DIRECTIONS_BUS_FILLED_OUTLINED,
            content_padding=ft.Padding.symmetric(horizontal=18, vertical=14),
            text_style=ft.TextStyle(
                size=19,
                weight=ft.FontWeight.W_700,
                color=INK,
            ),
            label_style=ft.TextStyle(
                size=13,
                weight=ft.FontWeight.W_600,
                color=MUTED,
            ),
            on_change=self._handle_change,
            on_submit=lambda _: self._try_submit(),
        )

        # Animated Status Validation Banner (implicit Flet animations: animate + animate_opacity)
        self.status_icon = ft.Icon(
            ft.Icons.VERIFIED_USER_ROUNDED,
            color=SUCCESS,
            size=22,
        )
        self.status_title = ft.Text(
            "Operador Vigente y Asignado",
            size=14,
            weight=ft.FontWeight.W_800,
            color=SUCCESS,
        )
        self.status_subtitle = ft.Text(
            "",
            size=12,
            weight=ft.FontWeight.W_600,
            color=INK,
        )
        self.status_unit_badge = ft.Container(
            padding=ft.Padding.symmetric(horizontal=10, vertical=5),
            border_radius=999,
            bgcolor="#DCFCE7",
            content=ft.Text(
                "ACTIVO",
                size=10,
                weight=ft.FontWeight.W_800,
                color=SUCCESS,
            ),
        )

        self.validation_container = ft.Container(
            opacity=0.0,
            animate_opacity=ft.Animation(280, ft.AnimationCurve.EASE_OUT_CUBIC),
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT_CUBIC),
            padding=ft.Padding.symmetric(horizontal=16, vertical=14),
            border_radius=14,
            bgcolor="#ECFDF5",
            border=ft.Border.all(1.5, "#A7F3D0"),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=40,
                                height=40,
                                border_radius=12,
                                bgcolor=WHITE,
                                alignment=ft.Alignment.CENTER,
                                content=self.status_icon,
                            ),
                            ft.Column(
                                spacing=2,
                                controls=[
                                    self.status_title,
                                    self.status_subtitle,
                                ],
                            ),
                        ],
                    ),
                    self.status_unit_badge,
                ],
            ),
        )

        self.continue_btn = ft.Button(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.SHIELD_OUTLINED, size=18, color=WHITE),
                    ft.Text(
                        "Continuar a Verificación de Identidad (INE)",
                        size=14,
                        weight=ft.FontWeight.W_700,
                        color=WHITE,
                    ),
                    ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, size=18, color=WHITE),
                ],
            ),
            height=52,
            disabled=not session.is_valid_assignment,
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.DEFAULT: BRAND,
                    ft.ControlState.DISABLED: LINE,
                },
                color={
                    ft.ControlState.DEFAULT: WHITE,
                    ft.ControlState.DISABLED: MUTED,
                },
                shape=ft.RoundedRectangleBorder(radius=14),
            ),
            on_click=lambda _: self._try_submit(),
        )

        self.qr_button = ft.OutlinedButton(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.QR_CODE_SCANNER_ROUNDED, size=20, color=BRAND),
                    ft.Text(
                        "Escanear Código QR (Acceso Rápido SITRAMYTEM)",
                        size=13,
                        weight=ft.FontWeight.W_700,
                        color=BRAND,
                    ),
                ],
            ),
            height=48,
            style=ft.ButtonStyle(
                bgcolor=BRAND_SOFT,
                side=ft.BorderSide(1.5, BRAND),
                shape=ft.RoundedRectangleBorder(radius=14),
            ),
            on_click=lambda _: self.on_open_qr(),
        )

        self.control = self._build()
        self.sync_from_session()

    def _handle_change(self, e: Optional[ft.ControlEvent] = None) -> None:
        folio_val = self.folio_input.value or ""
        plate_val = self.plate_input.value or ""
        self.on_credentials_change(folio_val, plate_val)

    def _fill_preset(self, folio: str, plate: str) -> None:
        self.folio_input.value = folio
        self.plate_input.value = plate
        self.on_credentials_change(folio, plate)

    def _try_submit(self) -> None:
        if self.session.is_valid_assignment:
            self.on_submit_login()

    def sync_from_session(self) -> None:
        if self.folio_input.value != self.session.folio and self.session.folio:
            self.folio_input.value = self.session.folio
        if self.plate_input.value != self.session.unit_plate and self.session.unit_plate:
            self.plate_input.value = self.session.unit_plate

        has_any_input = bool(
            (self.folio_input.value or "").strip() or (self.plate_input.value or "").strip()
        )

        if self.session.is_valid_assignment and self.session.vehicle:
            self.validation_container.opacity = 1.0
            self.validation_container.bgcolor = "#ECFDF5"
            self.validation_container.border = ft.Border.all(1.5, "#10B981")
            self.status_icon.name = ft.Icons.VERIFIED_ROUNDED
            self.status_icon.color = SUCCESS
            self.status_title.value = "Operador Vigente y Asignado"
            self.status_title.color = SUCCESS
            self.status_subtitle.value = (
                f"{self.session.operator_name} · Unidad {self.session.vehicle.economic_number} ({self.session.unit_plate})"
            )
            self.status_unit_badge.bgcolor = "#DCFCE7"
            self.status_unit_badge.content = ft.Text(
                "VIGENTE",
                size=10,
                weight=ft.FontWeight.W_800,
                color=SUCCESS,
            )
            self.continue_btn.disabled = False
        elif has_any_input:
            self.validation_container.opacity = 1.0
            self.validation_container.bgcolor = "#FFFBEB"
            self.validation_container.border = ft.Border.all(1.0, "#FCD34D")
            self.status_icon.name = ft.Icons.INFO_OUTLINE_ROUNDED
            self.status_icon.color = WARNING
            self.status_title.value = "Validando credenciales en padrón..."
            self.status_title.color = WARNING
            self.status_subtitle.value = self.session.status_label
            self.status_unit_badge.bgcolor = "#FEF3C7"
            self.status_unit_badge.content = ft.Text(
                "PENDIENTE",
                size=10,
                weight=ft.FontWeight.W_800,
                color=WARNING,
            )
            self.continue_btn.disabled = True
        else:
            self.validation_container.opacity = 0.0
            self.continue_btn.disabled = True

    def _build(self) -> ft.Container:
        quick_chips = ft.Row(
            spacing=8,
            wrap=True,
            controls=[
                ft.Text("Unidades asignadas hoy:", size=11, color=MUTED, weight=ft.FontWeight.W_600),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=10, vertical=5),
                    border_radius=999,
                    bgcolor=SOFT,
                    border=ft.Border.all(1, LINE),
                    on_click=lambda _: self._fill_preset("84021", "MEX-1234"),
                    content=ft.Text("Folio 84021 · MEX-1234", size=11, weight=ft.FontWeight.W_700, color=INK),
                ),
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=10, vertical=5),
                    border_radius=999,
                    bgcolor=SOFT,
                    border=ft.Border.all(1, LINE),
                    on_click=lambda _: self._fill_preset("10492", "MEX-2048"),
                    content=ft.Text("Folio 10492 · MEX-2048", size=11, weight=ft.FontWeight.W_700, color=INK),
                ),
            ],
        )

        return ft.Container(
            width=480,
            padding=24,
            border_radius=22,
            bgcolor=WHITE,
            border=ft.Border.all(1, LINE),
            shadow=shadow(),
            content=ft.Column(
                spacing=16,
                tight=True,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                spacing=10,
                                controls=[
                                    ft.Container(
                                        width=38,
                                        height=38,
                                        border_radius=11,
                                        bgcolor=BRAND_SOFT,
                                        alignment=ft.Alignment.CENTER,
                                        content=ft.Icon(ft.Icons.DIRECTIONS_BUS_ROUNDED, color=BRAND, size=20),
                                    ),
                                    ft.Column(
                                        spacing=1,
                                        controls=[
                                            ft.Text(
                                                "AUTENTICACIÓN DE OPERADOR",
                                                size=11,
                                                weight=ft.FontWeight.W_800,
                                                color=BRAND,
                                            ),
                                            ft.Text(
                                                "Vinculación de Turno y Unidad BRT",
                                                size=18,
                                                weight=ft.FontWeight.W_800,
                                                color=INK,
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                            ft.Container(
                                padding=ft.Padding.symmetric(horizontal=10, vertical=5),
                                border_radius=999,
                                bgcolor=SOFT,
                                content=ft.Text(
                                    "LÍNEA 2",
                                    size=11,
                                    weight=ft.FontWeight.W_800,
                                    color=INK,
                                ),
                            ),
                        ],
                    ),
                    ft.Text(
                        "Ingresa tu Folio Único de empleado y la matrícula de la unidad física que conducirás en este turno, o utiliza el escáner QR oficial.",
                        size=13,
                        color=MUTED,
                    ),
                    self.folio_input,
                    self.plate_input,
                    quick_chips,
                    self.validation_container,
                    self.continue_btn,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            ft.Container(height=1, width=90, bgcolor=LINE),
                            ft.Text("O ACCESO INMEDIATO", size=10, weight=ft.FontWeight.W_700, color=MUTED),
                            ft.Container(height=1, width=90, bgcolor=LINE),
                        ],
                    ),
                    self.qr_button,
                ],
            ),
        )
