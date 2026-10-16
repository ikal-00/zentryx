from typing import Callable
import flet as ft

from app.models_driver import IneDocumentState
from app.theme import (
    BRAND,
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


class IneCaptureSideCard:
    """
    Tarjeta de captura individual (Anverso o Reverso de INE) con:
    - Vista previa en vivo de la imagen capturada (ft.Image + metadatos de captura).
    - Botón primario: 'Abrir Cámara y Capturar'.
    - Botón secundario estilizado de respaldo: 'Subir desde Galería'.
    """

    def __init__(
        self,
        side: str,
        title: str,
        subtitle: str,
        on_camera_click: Callable[[str], None],
        on_gallery_click: Callable[[str], None],
    ):
        self.side = side
        self.title = title
        self.subtitle = subtitle
        self.on_camera_click = on_camera_click
        self.on_gallery_click = on_gallery_click

        self.badge = ft.Container(
            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
            border_radius=999,
            bgcolor=SOFT,
            content=ft.Text(
                "PENDIENTE",
                size=10,
                weight=ft.FontWeight.W_800,
                color=MUTED,
            ),
        )

        self.preview_image = ft.Image(
            src="",
            width=410,
            height=155,
            fit=ft.BoxFit.CONTAIN,
            border_radius=12,
            visible=False,
        )

        self.empty_placeholder = ft.Container(
            height=135,
            border_radius=14,
            bgcolor=PAPER,
            border=ft.Border.all(1.5, LINE),
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Icon(
                        ft.Icons.BADGE_OUTLINED if side == "front" else ft.Icons.QR_CODE_SCANNER_ROUNDED,
                        size=34,
                        color=MUTED,
                    ),
                    ft.Text(
                        f"Sin captura de {title.lower()}",
                        size=12,
                        weight=ft.FontWeight.W_700,
                        color=INK,
                    ),
                    ft.Text(
                        subtitle,
                        size=11,
                        color=MUTED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            ),
        )

        self.file_caption = ft.Text(
            "",
            size=11,
            weight=ft.FontWeight.W_600,
            color=SUCCESS,
            visible=False,
        )

        self.camera_btn = ft.Button(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.CAMERA_ALT_ROUNDED, size=16, color=WHITE),
                    ft.Text(
                        "Abrir Cámara",
                        size=12,
                        weight=ft.FontWeight.W_700,
                        color=WHITE,
                    ),
                ],
            ),
            height=42,
            expand=True,
            style=ft.ButtonStyle(
                bgcolor=BRAND,
                color=WHITE,
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            on_click=lambda _: self.on_camera_click(self.side),
        )

        self.gallery_btn = ft.OutlinedButton(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.PHOTO_LIBRARY_OUTLINED, size=16, color=INK),
                    ft.Text(
                        "Subir desde Galería",
                        size=12,
                        weight=ft.FontWeight.W_700,
                        color=INK,
                    ),
                ],
            ),
            height=42,
            expand=True,
            style=ft.ButtonStyle(
                bgcolor=WHITE,
                side=ft.BorderSide(1.2, LINE),
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            on_click=lambda _: self.on_gallery_click(self.side),
        )

        self.control = ft.Container(
            padding=18,
            border_radius=18,
            bgcolor=WHITE,
            border=ft.Border.all(1.2, LINE),
            animate=ft.Animation(260, ft.AnimationCurve.EASE_OUT_CUBIC),
            content=ft.Column(
                spacing=12,
                tight=True,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Container(
                                        width=30,
                                        height=30,
                                        border_radius=9,
                                        bgcolor=BRAND_SOFT,
                                        alignment=ft.Alignment.CENTER,
                                        content=ft.Text(
                                            "1" if side == "front" else "2",
                                            size=13,
                                            weight=ft.FontWeight.W_800,
                                            color=BRAND,
                                        ),
                                    ),
                                    ft.Text(
                                        title,
                                        size=15,
                                        weight=ft.FontWeight.W_800,
                                        color=INK,
                                    ),
                                ],
                            ),
                            self.badge,
                        ],
                    ),
                    self.empty_placeholder,
                    self.preview_image,
                    self.file_caption,
                    ft.Row(
                        spacing=10,
                        controls=[
                            self.camera_btn,
                            self.gallery_btn,
                        ],
                    ),
                ],
            ),
        )

    def sync(
        self,
        captured: bool,
        source: str | None,
        preview_uri: str | None,
        filename: str | None,
    ) -> None:
        if captured and preview_uri:
            self.empty_placeholder.visible = False
            self.preview_image.src = preview_uri
            self.preview_image.visible = True
            self.file_caption.value = (
                f"✓ Imagen previsualizada ({'Cámara' if source == 'camera' else 'Galería'}): {filename}"
            )
            self.file_caption.visible = True
            self.badge.bgcolor = "#DCFCE7"
            self.badge.content = ft.Text(
                "CAPTURADO",
                size=10,
                weight=ft.FontWeight.W_800,
                color=SUCCESS,
            )
            self.control.border = ft.Border.all(1.5, "#10B981")
        else:
            self.empty_placeholder.visible = True
            self.preview_image.visible = False
            self.file_caption.visible = False
            self.badge.bgcolor = SOFT
            self.badge.content = ft.Text(
                "PENDIENTE",
                size=10,
                weight=ft.FontWeight.W_800,
                color=MUTED,
            )
            self.control.border = ft.Border.all(1.2, LINE)


class IneVerificationSkeletonLoader:
    """
    Skeleton Loader y barra de progreso asíncrona no bloqueante
    mientras las fotografías de la INE se verifican contra el padrón biométrico.
    """

    def __init__(self):
        self.step_label = ft.Text(
            "Analizando hologramas y biometría facial...",
            size=13,
            weight=ft.FontWeight.W_700,
            color=INK,
        )
        self.percent_label = ft.Text(
            "0%",
            size=13,
            weight=ft.FontWeight.W_800,
            color=BRAND,
        )
        self.progress_bar = ft.ProgressBar(
            value=0.0,
            color=BRAND,
            bgcolor=BRAND_SOFT,
            height=8,
            border_radius=999,
        )

        # Animated skeleton lines simulating OCR / MRZ field extraction
        self.skel_bar_1 = ft.Container(
            height=12,
            width=280,
            border_radius=6,
            bgcolor=SOFT,
            animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
        )
        self.skel_bar_2 = ft.Container(
            height=12,
            width=210,
            border_radius=6,
            bgcolor=SOFT,
            animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
        )

        self.control = ft.Container(
            visible=False,
            padding=18,
            border_radius=16,
            bgcolor="#FFF5F6",
            border=ft.Border.all(1.5, BRAND),
            animate_opacity=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
            content=ft.Column(
                spacing=10,
                tight=True,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                spacing=10,
                                controls=[
                                    ft.ProgressRing(
                                        width=18,
                                        height=18,
                                        stroke_width=2.5,
                                        color=BRAND,
                                    ),
                                    self.step_label,
                                ],
                            ),
                            self.percent_label,
                        ],
                    ),
                    self.progress_bar,
                    ft.Column(
                        spacing=6,
                        controls=[
                            self.skel_bar_1,
                            self.skel_bar_2,
                        ],
                    ),
                ],
            ),
        )

    def sync(self, ine: IneDocumentState) -> None:
        self.control.visible = ine.verifying
        self.progress_bar.value = ine.verification_progress
        self.percent_label.value = f"{int(ine.verification_progress * 100)}%"
        self.step_label.value = ine.verification_step_label
        # Pulse skeleton opacity based on progress step
        self.skel_bar_1.opacity = 0.45 if int(ine.verification_progress * 10) % 2 == 0 else 0.95
        self.skel_bar_2.opacity = 0.95 if int(ine.verification_progress * 10) % 2 == 0 else 0.45
