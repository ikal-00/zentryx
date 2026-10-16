import asyncio
from typing import Callable
import flet as ft

from app.services.driver_service import simulate_qr_scan_payload
from app.theme import (
    BRAND,
    BRAND_SOFT,
    INK,
    LINE,
    MUTED,
    SOFT,
    SUCCESS,
    WHITE,
)


def build_qr_scanner_dialog(
    page: ft.Page,
    on_qr_verified: Callable[[str, str, str], None],
) -> ft.AlertDialog:
    """
    Construye el modal de Escáner QR para validar el estatus del operador en la
    plataforma oficial del transporte mexiquense (SITRAMYTEM).
    Incluye visor de cámara simulado a 60fps y validación instantánea.
    """
    status_text = ft.Text(
        "Apunta la cámara al código QR de tu Gafete Único de Operador o Tarjeta de Circulación BRT",
        size=12,
        color=MUTED,
        text_align=ft.TextAlign.CENTER,
    )

    scan_badge = ft.Container(
        padding=ft.Padding.symmetric(horizontal=12, vertical=6),
        border_radius=999,
        bgcolor="#1F2430",
        content=ft.Row(
            tight=True,
            spacing=6,
            controls=[
                ft.Icon(ft.Icons.VIDEOCAM_ROUNDED, size=14, color="#10B981"),
                ft.Text(
                    "CÁMARA ÓPTICA ACTIVA · 60 FPS",
                    size=10,
                    weight=ft.FontWeight.W_800,
                    color=WHITE,
                ),
            ],
        ),
    )

    laser_line = ft.Container(
        width=230,
        height=3,
        border_radius=999,
        bgcolor=BRAND,
        animate=ft.Animation(450, ft.AnimationCurve.EASE_IN_OUT),
    )

    viewfinder_box = ft.Container(
        width=280,
        height=210,
        border_radius=18,
        bgcolor=INK,
        border=ft.Border.all(2, BRAND),
        padding=18,
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                scan_badge,
                ft.Icon(ft.Icons.QR_CODE_2_ROUNDED, size=76, color=WHITE),
                laser_line,
                ft.Text(
                    "SITRAMYTEM · PADRÓN ESTATAL",
                    size=10,
                    weight=ft.FontWeight.W_700,
                    color="#9CA3AF",
                ),
            ],
        ),
    )

    def trigger_scan(preset_idx: int) -> None:
        folio, plate, token = simulate_qr_scan_payload(preset_idx)
        status_text.value = f"✓ QR Verificado: {token}"
        status_text.color = SUCCESS
        viewfinder_box.border = ft.Border.all(2.5, "#10B981")
        page.pop_dialog()
        on_qr_verified(folio, plate, token)

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor=WHITE,
        title=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Icon(ft.Icons.QR_CODE_SCANNER_ROUNDED, color=BRAND, size=22),
                        ft.Text(
                            "Escáner QR Oficial",
                            size=18,
                            weight=ft.FontWeight.W_800,
                            color=INK,
                        ),
                    ],
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOSE_ROUNDED,
                    icon_color=MUTED,
                    tooltip="Cerrar escáner",
                    on_click=lambda _: page.pop_dialog(),
                ),
            ],
        ),
        content=ft.Container(
            width=360,
            content=ft.Column(
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=14,
                controls=[
                    viewfinder_box,
                    status_text,
                    ft.Container(
                        padding=12,
                        border_radius=12,
                        bgcolor=SOFT,
                        border=ft.Border.all(1, LINE),
                        content=ft.Column(
                            spacing=8,
                            controls=[
                                ft.Text(
                                    "LECTURA DE CREDENCIAL OFICIAL EN CÁMARA:",
                                    size=10,
                                    weight=ft.FontWeight.W_800,
                                    color=MUTED,
                                ),
                                ft.Button(
                                    content=ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        spacing=8,
                                        controls=[
                                            ft.Icon(ft.Icons.CENTER_FOCUS_STRONG_ROUNDED, size=18, color=WHITE),
                                            ft.Text(
                                                "Capturar QR Operador #84021 (MEX-1234)",
                                                size=12,
                                                weight=ft.FontWeight.W_700,
                                                color=WHITE,
                                            ),
                                        ],
                                    ),
                                    style=ft.ButtonStyle(
                                        bgcolor=BRAND,
                                        color=WHITE,
                                        shape=ft.RoundedRectangleBorder(radius=10),
                                    ),
                                    on_click=lambda _: trigger_scan(0),
                                ),
                                ft.OutlinedButton(
                                    content=ft.Text(
                                        "Capturar QR Operador #10492 (MEX-2048)",
                                        size=12,
                                        weight=ft.FontWeight.W_700,
                                        color=INK,
                                    ),
                                    style=ft.ButtonStyle(
                                        bgcolor=WHITE,
                                        side=ft.BorderSide(1, LINE),
                                        shape=ft.RoundedRectangleBorder(radius=10),
                                    ),
                                    on_click=lambda _: trigger_scan(1),
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        ),
    )
    return dialog
