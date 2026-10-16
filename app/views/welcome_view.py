from typing import Callable
import flet as ft

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
    WHITE,
    shadow,
)


class WelcomeView:
    """
    Interfaz de Inicio unificada de Zentryx en Flet.
    Presenta:
    1. Opción Principal: 'Ver mapa y unidades' (Modo Pasajero).
    2. Opción Extra: 'Modo Conductor' (Pasa primero por Verificación de Datos + INE
       y luego redirige a la misma interfaz de mapa y telemetría de la unidad con el apartado de Botón de Emergencia).
    """

    def __init__(
        self,
        on_select_passenger: Callable[[], None],
        on_select_driver: Callable[[], None],
    ):
        self.on_select_passenger = on_select_passenger
        self.on_select_driver = on_select_driver
        self.control = self._build()

    def _mode_card(
        self,
        title: str,
        subtitle: str,
        icon_name,
        primary: bool,
        on_click: Callable[[], None],
        badge_text: str | None = None,
    ) -> ft.Container:
        fg = WHITE if primary else INK
        sub_fg = "#FDEBED" if primary else MUTED
        bg = BRAND_STRONG if primary else WHITE
        border = None if primary else ft.Border.all(1.5, LINE)

        title_row_controls = [
            ft.Text(
                title,
                size=18,
                weight=ft.FontWeight.W_800,
                color=fg,
            )
        ]
        if badge_text:
            title_row_controls.append(
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    border_radius=999,
                    bgcolor=BRAND_SOFT if not primary else BRAND_DARK,
                    content=ft.Text(
                        badge_text,
                        size=9,
                        weight=ft.FontWeight.W_800,
                        color=BRAND if not primary else WHITE,
                    ),
                )
            )

        return ft.Container(
            padding=20,
            border_radius=20,
            bgcolor=bg,
            border=border,
            shadow=shadow(),
            on_click=lambda _: on_click(),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        spacing=14,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True,
                        controls=[
                            ft.Container(
                                width=46,
                                height=46,
                                border_radius=14,
                                bgcolor=BRAND_DARK if primary else BRAND_SOFT,
                                alignment=ft.Alignment.CENTER,
                                content=ft.Icon(
                                    icon_name,
                                    size=24,
                                    color=WHITE if primary else BRAND,
                                ),
                            ),
                            ft.Column(
                                spacing=4,
                                expand=True,
                                controls=[
                                    ft.Row(
                                        spacing=8,
                                        wrap=True,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        controls=title_row_controls,
                                    ),
                                    ft.Text(
                                        subtitle,
                                        size=12,
                                        color=sub_fg,
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.Icon(
                        ft.Icons.ARROW_OUTWARD_ROUNDED,
                        size=20,
                        color=fg,
                    ),
                ],
            ),
        )

    def _build(self) -> ft.Container:
        line_hero = ft.Container(
            padding=20,
            border_radius=20,
            bgcolor=WHITE,
            border=ft.Border.all(1, LINE),
            shadow=shadow(),
            content=ft.Column(
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.Container(
                                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                                border_radius=10,
                                bgcolor=BRAND_SOFT,
                                content=ft.Text(
                                    "L2",
                                    size=13,
                                    weight=ft.FontWeight.W_800,
                                    color=BRAND_DARK,
                                ),
                            ),
                            ft.Text(
                                "Mexibús Línea 2",
                                size=16,
                                weight=ft.FontWeight.W_800,
                                color=INK,
                            ),
                        ],
                    ),
                    ft.Text(
                        "Las Américas ⇄ La Quebrada · Seguimiento y telemetría de unidad en tiempo real",
                        size=12,
                        color=MUTED,
                    ),
                ],
            ),
        )

        return ft.Container(
            expand=True,
            bgcolor=PAPER,
            alignment=ft.Alignment.CENTER,
            padding=20,
            content=ft.Container(
                width=460,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    spacing=18,
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Row(
                            spacing=12,
                            controls=[
                                ft.Container(
                                    width=42,
                                    height=42,
                                    border_radius=12,
                                    bgcolor=INK,
                                    alignment=ft.Alignment.CENTER,
                                    content=ft.Icon(
                                        ft.Icons.NEAR_ME_ROUNDED,
                                        color=BRAND_STRONG,
                                        size=22,
                                    ),
                                ),
                                ft.Column(
                                    spacing=1,
                                    controls=[
                                        ft.Text(
                                            "ZENTRYX",
                                            size=20,
                                            weight=ft.FontWeight.W_900,
                                            color=INK,
                                        ),
                                        ft.Text(
                                            "Movilidad en tiempo real",
                                            size=12,
                                            color=MUTED,
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        ft.Column(
                            spacing=6,
                            controls=[
                                ft.Text(
                                    "Tu ciudad.\nA tu ritmo.",
                                    size=34,
                                    weight=ft.FontWeight.W_800,
                                    color=INK,
                                ),
                                ft.Text(
                                    "Selecciona tu modo de acceso a la plataforma.",
                                    size=14,
                                    color=MUTED,
                                ),
                            ],
                        ),
                        line_hero,
                        ft.Text(
                            "SELECCIONA MODO DE OPERACIÓN",
                            size=11,
                            weight=ft.FontWeight.W_800,
                            color=MUTED,
                        ),
                        self._mode_card(
                            title="Ver mapa y unidades",
                            subtitle="Modo Pasajero · Consulta estaciones, tiempos de llegada y seguimiento en vivo",
                            icon_name=ft.Icons.MAP_ROUNDED,
                            primary=True,
                            on_click=self.on_select_passenger,
                        ),
                        self._mode_card(
                            title="Modo conductor",
                            subtitle="Verificación de datos e INE · Misma interfaz y telemetría de unidad con botón de emergencia SOS",
                            icon_name=ft.Icons.BADGE_OUTLINED,
                            primary=False,
                            badge_text="OPERADOR VERIFICADO",
                            on_click=self.on_select_driver,
                        ),
                    ],
                ),
            ),
        )
