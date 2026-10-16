import asyncio
from typing import Callable, Optional
import flet as ft

from app.models_driver import EmergencyAlertPayload
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


class PanicSecurityModule:
    """
    Módulo de Seguridad: Botón de Pánico / Reporte de Emergencias con Fricción Intencional.
    Cumple con:
    1. Botón rojo altamente visible en el Header del dashboard + Panel de Seguridad.
    2. Fricción Intencional Anti-toques accidentales:
       - NO se activa con un simple tap (muestra aviso preventivo).
       - Opción A: Mantener presionado por 3 segundos (con anillo de carga ft.ProgressRing llenándose a 60fps).
       - Opción B: Deslizar para confirmar (Slider personalizado al 100%).
    3. Acción Posterior: Muestra Banner persistente no obstructivo + SnackBar con coordenadas actuales.
    """

    HOLD_DURATION_SECONDS = 3.0
    TICK_SECONDS = 0.05  # 20Hz / smooth ring progression

    def __init__(
        self,
        page: ft.Page,
        on_trigger_emergency: Callable[[str], EmergencyAlertPayload],
    ):
        self.page = page
        self.on_trigger_emergency = on_trigger_emergency
        self._holding = False
        self._hold_progress = 0.0
        self._dispatched_alert: Optional[EmergencyAlertPayload] = None

        # Header compact SOS button (Hold for 3s or opens emergency modal on single tap warning)
        self.header_ring = ft.ProgressRing(
            value=0.0,
            width=20,
            height=20,
            stroke_width=2.5,
            color=WHITE,
            bgcolor="#7A091D",
        )
        self.header_label = ft.Text(
            "SOS · MANTENER 3S",
            size=11,
            weight=ft.FontWeight.W_800,
            color=WHITE,
        )

        self.header_sos_button = ft.GestureDetector(
            on_tap=self._on_accidental_single_tap,
            on_long_press_start=self._on_hold_start,
            on_long_press_end=self._on_hold_end,
            on_pan_cancel=self._on_hold_cancel,
            content=ft.Container(
                padding=ft.Padding.symmetric(horizontal=14, vertical=8),
                border_radius=999,
                bgcolor=BRAND,
                border=ft.Border.all(1.5, "#FF4D6D"),
                shadow=shadow(),
                content=ft.Row(
                    spacing=8,
                    tight=True,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self.header_ring,
                        ft.Icon(ft.Icons.EMERGENCY_SHARE_ROUNDED, color=WHITE, size=16),
                        self.header_label,
                    ],
                ),
            ),
        )

        # Main Dashboard Hold-for-3s Ring Control
        self.main_ring = ft.ProgressRing(
            value=0.0,
            width=84,
            height=84,
            stroke_width=7,
            color=WHITE,
            bgcolor="#8E0B23",
        )
        self.hold_countdown_text = ft.Text(
            "MANTENER 3.0s",
            size=12,
            weight=ft.FontWeight.W_800,
            color=WHITE,
        )
        self.hold_hint_text = ft.Text(
            "Protección anti-toques accidentales activa: mantén presionado 3 segundos o desliza la barra inferior.",
            size=12,
            color=MUTED,
        )

        self.hold_button_container = ft.Container(
            height=110,
            border_radius=20,
            bgcolor=BRAND,
            border=ft.Border.all(2, BRAND_DARK),
            padding=16,
            shadow=shadow(),
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=16,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Stack(
                                width=84,
                                height=84,
                                alignment=ft.Alignment.CENTER,
                                controls=[
                                    self.main_ring,
                                    ft.Container(
                                        width=64,
                                        height=64,
                                        border_radius=999,
                                        bgcolor=BRAND_DARK,
                                        alignment=ft.Alignment.CENTER,
                                        content=ft.Icon(
                                            ft.Icons.SOS_ROUNDED,
                                            size=32,
                                            color=WHITE,
                                        ),
                                    ),
                                ],
                            ),
                            ft.Column(
                                spacing=4,
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Text(
                                        "BOTÓN DE PÁNICO / EMERGENCIA C5",
                                        size=15,
                                        weight=ft.FontWeight.W_800,
                                        color=WHITE,
                                    ),
                                    ft.Text(
                                        "Mantén presionado durante 3 segundos continuos",
                                        size=12,
                                        color="#FDEBED",
                                    ),
                                    self.hold_countdown_text,
                                ],
                            ),
                        ],
                    ),
                    ft.Icon(ft.Icons.TOUCH_APP_ROUNDED, color=WHITE, size=28),
                ],
            ),
        )

        self.hold_gesture_card = ft.GestureDetector(
            on_tap=self._on_accidental_single_tap,
            on_tap_down=self._on_hold_start,
            on_tap_up=self._on_hold_end,
            on_long_press_start=self._on_hold_start,
            on_long_press_end=self._on_hold_end,
            on_pan_end=self._on_hold_end,
            on_pan_cancel=self._on_hold_cancel,
            content=self.hold_button_container,
        )

        # Secondary Intentional Friction: Custom Slide-to-Confirm Slider
        self.slider_label = ft.Text(
            "Deslizar al 100% para confirmar envío inmediato a Central",
            size=12,
            weight=ft.FontWeight.W_700,
            color=BRAND_DARK,
        )
        self.confirm_slider = ft.Slider(
            min=0,
            max=100,
            value=0,
            divisions=20,
            active_color=BRAND,
            inactive_color=BRAND_SOFT,
            thumb_color=BRAND_DARK,
            on_change=self._on_slider_change,
            on_change_end=self._on_slider_release,
        )

        # Persistent Non-Obstructive Emergency Alert Banner
        self.banner_title = ft.Text(
            "Alerta enviada a Central con coordenadas actuales",
            size=13,
            weight=ft.FontWeight.W_800,
            color=WHITE,
        )
        self.banner_details = ft.Text(
            "",
            size=12,
            color="#FDEBED",
        )
        self.persistent_alert_banner = ft.Container(
            visible=False,
            padding=ft.Padding.symmetric(horizontal=18, vertical=14),
            border_radius=16,
            bgcolor="#7A091D",
            border=ft.Border.all(1.5, BRAND),
            shadow=shadow(),
            animate_opacity=ft.Animation(280, ft.AnimationCurve.EASE_OUT),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=38,
                                height=38,
                                border_radius=10,
                                bgcolor=BRAND,
                                alignment=ft.Alignment.CENTER,
                                content=ft.Icon(ft.Icons.GTE_MOBILEDATA_ROUNDED if hasattr(ft.Icons, "GTE_MOBILEDATA_ROUNDED") else ft.Icons.SATELLITE_ALT_ROUNDED, color=WHITE, size=20),
                            ),
                            ft.Column(
                                spacing=2,
                                controls=[
                                    self.banner_title,
                                    self.banner_details,
                                ],
                            ),
                        ],
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE_ROUNDED,
                        icon_color=WHITE,
                        tooltip="Ocultar aviso persistente",
                        on_click=self._dismiss_banner,
                    ),
                ],
            ),
        )

        self.panel_control = self._build_panel()

    def _on_accidental_single_tap(self, _=None) -> None:
        """
        Fricción intencional: un simple tap NO dispara la alarma.
        """
        if not self._holding:
            self.hold_hint_text.value = (
                "⚠ Toque corto ignorado por seguridad. Mantén presionado 3 segundos o desliza el control al 100%."
            )
            self.hold_hint_text.color = WARNING
            self.page.update()

    def _on_hold_start(self, _=None) -> None:
        if self._holding:
            return
        self._holding = True
        self._hold_progress = 0.0
        self.hold_button_container.bgcolor = BRAND_STRONG
        self.page.run_task(self._run_hold_timer)

    def _on_hold_end(self, _=None) -> None:
        if self._holding and self._hold_progress < 1.0:
            self._cancel_hold()

    def _on_hold_cancel(self, _=None) -> None:
        if self._holding and self._hold_progress < 1.0:
            self._cancel_hold()

    def _cancel_hold(self) -> None:
        self._holding = False
        self._hold_progress = 0.0
        self.main_ring.value = 0.0
        self.header_ring.value = 0.0
        self.hold_countdown_text.value = "MANTENER 3.0s"
        self.header_label.value = "SOS · MANTENER 3S"
        self.hold_button_container.bgcolor = BRAND
        self.hold_hint_text.value = (
            "Liberado antes de 3 segundos: envío cancelado para evitar falsa alarma."
        )
        self.hold_hint_text.color = MUTED
        self.page.update()

    async def _run_hold_timer(self) -> None:
        elapsed = 0.0
        while self._holding and elapsed < self.HOLD_DURATION_SECONDS:
            await asyncio.sleep(self.TICK_SECONDS)
            if not self._holding:
                return
            elapsed += self.TICK_SECONDS
            self._hold_progress = min(1.0, elapsed / self.HOLD_DURATION_SECONDS)
            remaining = max(0.0, self.HOLD_DURATION_SECONDS - elapsed)
            self.main_ring.value = self._hold_progress
            self.header_ring.value = self._hold_progress
            self.hold_countdown_text.value = f"ACTIVANDO EN {remaining:.1f}s..."
            self.header_label.value = f"SOS {remaining:.1f}s"
            self.page.update()

        if self._holding and self._hold_progress >= 1.0:
            self._holding = False
            self.trigger_alert(method="hold_3s")

    def _on_slider_change(self, e: ft.ControlEvent) -> None:
        val = float(self.confirm_slider.value or 0)
        if val > 10:
            self.slider_label.value = f"Deslizando confirmación de emergencia... {int(val)}%"
            self.page.update()

    def _on_slider_release(self, e: ft.ControlEvent) -> None:
        val = float(self.confirm_slider.value or 0)
        if val >= 95.0:
            self.confirm_slider.value = 100
            self.trigger_alert(method="slide_confirm")
        else:
            self.confirm_slider.value = 0
            self.slider_label.value = "Deslizar al 100% para confirmar envío inmediato a Central"
            self.page.update()

    def trigger_alert(self, method: str = "hold_3s") -> EmergencyAlertPayload:
        alert = self.on_trigger_emergency(method)
        self._dispatched_alert = alert

        self.main_ring.value = 1.0
        self.header_ring.value = 1.0
        self.hold_countdown_text.value = "✓ ALERTA DESPACHADA A CENTRAL"
        self.header_label.value = "ALERTA ACTIVA"
        self.hold_button_container.bgcolor = "#0F7644"

        method_text = "Mantener 3s" if method == "hold_3s" else "Deslizar para confirmar"
        self.banner_title.value = "Alerta enviada a Central con coordenadas actuales"
        self.banner_details.value = (
            f"Folio {alert.alert_id} · Unidad {alert.unit_plate} ({alert.economic_number}) · "
            f"GPS ({alert.latitude:.5f}, {alert.longitude:.5f}) · Estación {alert.station_context} · Vía {method_text}"
        )
        self.persistent_alert_banner.visible = True
        self.hold_hint_text.value = (
            f"✓ Alerta {alert.alert_id} recibida por Central C5 a las {alert.timestamp_iso}."
        )
        self.hold_hint_text.color = SUCCESS

        # Also trigger SnackBar if supported on page
        try:
            snack = ft.SnackBar(
                bgcolor=INK,
                content=ft.Text(
                    f"🚨 Alerta enviada a Central con coordenadas actuales ({alert.latitude:.4f}, {alert.longitude:.4f})",
                    color=WHITE,
                    weight=ft.FontWeight.W_700,
                ),
                open=True,
            )
            if hasattr(self.page, "overlay") and isinstance(self.page.overlay, list):
                self.page.overlay.append(snack)
        except Exception:
            pass

        self.page.update()
        return alert

    def _dismiss_banner(self, _=None) -> None:
        self.persistent_alert_banner.visible = False
        self.confirm_slider.value = 0
        self.main_ring.value = 0.0
        self.header_ring.value = 0.0
        self.hold_button_container.bgcolor = BRAND
        self.hold_countdown_text.value = "MANTENER 3.0s"
        self.header_label.value = "SOS · MANTENER 3S"
        self.page.update()

    def _build_panel(self) -> ft.Container:
        return ft.Container(
            padding=20,
            border_radius=22,
            bgcolor=WHITE,
            border=ft.Border.all(1.5, LINE),
            shadow=shadow(),
            content=ft.Column(
                spacing=14,
                tight=True,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Icon(ft.Icons.SHIELD_ROUNDED, color=BRAND, size=20),
                                    ft.Text(
                                        "PROTOCOLO DE SEGURIDAD Y EMERGENCIAS",
                                        size=12,
                                        weight=ft.FontWeight.W_800,
                                        color=BRAND,
                                    ),
                                ],
                            ),
                            ft.Container(
                                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                                border_radius=999,
                                bgcolor=BRAND_SOFT,
                                content=ft.Text(
                                    "ANTI-TOQUE ACCIDENTAL",
                                    size=10,
                                    weight=ft.FontWeight.W_800,
                                    color=BRAND,
                                ),
                            ),
                        ],
                    ),
                    self.hold_gesture_card,
                    self.hold_hint_text,
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=14, vertical=10),
                        border_radius=14,
                        bgcolor=PAPER,
                        border=ft.Border.all(1, LINE),
                        content=ft.Column(
                            spacing=4,
                            tight=True,
                            controls=[
                                self.slider_label,
                                self.confirm_slider,
                            ],
                        ),
                    ),
                ],
            ),
        )
