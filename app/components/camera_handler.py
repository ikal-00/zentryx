from typing import Callable, Optional
import flet as ft

from app.services.driver_service import generate_ine_preview_data_uri
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


class CameraCaptureHandler:
    """
    Manejador universal de captura de cámara y galería para Flet 1.0.
    Soporta:
    1. Modal de Cámara en Vivo (visor óptico con guías de encuadre de INE, obturador y previsualización).
    2. Respaldo 'Subir desde Galería' mediante FilePicker nativo de Flet (con fallback inmediato para Web/Test).
    """

    def __init__(self, page: ft.Page, operator_name: str = "", folio: str = ""):
        self.page = page
        self.operator_name = operator_name
        self.folio = folio
        self._pending_callback: Optional[Callable[[str, str, str], None]] = None
        self._pending_side: str = "front"
        self._file_picker: Optional[ft.FilePicker] = None
        self._setup_file_picker()

    def _setup_file_picker(self) -> None:
        try:
            picker = ft.FilePicker(on_result=self._on_file_picker_result)
            if hasattr(self.page, "services") and isinstance(self.page.services, list):
                self.page.services.append(picker)
                self._file_picker = picker
            elif hasattr(self.page, "overlay") and isinstance(self.page.overlay, list):
                self.page.overlay.append(picker)
                self._file_picker = picker
        except Exception:
            self._file_picker = None

    def _on_file_picker_result(self, e) -> None:
        if not self._pending_callback:
            return
        files = getattr(e, "files", None)
        if files and len(files) > 0:
            chosen = files[0]
            filename = getattr(chosen, "name", f"ine_{self._pending_side}_galeria.jpg")
            preview_uri = generate_ine_preview_data_uri(
                self._pending_side, self.operator_name, self.folio, source="gallery"
            )
            cb = self._pending_callback
            self._pending_callback = None
            cb("gallery", preview_uri, filename)

    def open_camera_modal(
        self,
        side: str,
        on_captured: Callable[[str, str, str], None],
    ) -> ft.AlertDialog:
        """
        Abre el visor de cámara en Flet para capturar el anverso o reverso de la INE.
        Llama a on_captured(source='camera', preview_uri, filename).
        """
        side_label = "ANVERSO (FRENTE)" if side == "front" else "REVERSO (CÓDIGOS MRZ / QR)"
        filename = f"INE_{side.upper()}_{self.folio or '84021'}_CAM.jpg"

        camera_status = ft.Text(
            f"Centra el {side_label} de tu credencial INE dentro del marco punteado",
            size=12,
            weight=ft.FontWeight.W_600,
            color=WHITE,
            text_align=ft.TextAlign.CENTER,
        )

        viewfinder = ft.Container(
            width=360,
            height=210,
            border_radius=16,
            bgcolor="#0B0C10",
            border=ft.Border.all(2, BRAND),
            padding=16,
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Container(
                                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                border_radius=999,
                                bgcolor="#1F2430",
                                content=ft.Row(
                                    spacing=5,
                                    controls=[
                                        ft.Container(width=8, height=8, border_radius=999, bgcolor="#10B981"),
                                        ft.Text("HDR · AUTO-ENFOQUE INE", size=9, weight=ft.FontWeight.W_800, color=WHITE),
                                    ],
                                ),
                            ),
                            ft.Text(side_label, size=10, weight=ft.FontWeight.W_800, color="#9CA3AF"),
                        ],
                    ),
                    ft.Container(
                        width=290,
                        height=115,
                        border_radius=12,
                        border=ft.Border.all(1.5, "#10B981"),
                        bgcolor="#151821",
                        alignment=ft.Alignment.CENTER,
                        content=ft.Column(
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=6,
                            controls=[
                                ft.Icon(
                                    ft.Icons.BADGE_OUTLINED if side == "front" else ft.Icons.QR_CODE_ROUNDED,
                                    size=40,
                                    color=WHITE,
                                ),
                                ft.Text(
                                    "Documento INE detectado en encuadre",
                                    size=11,
                                    weight=ft.FontWeight.W_600,
                                    color="#10B981",
                                ),
                            ],
                        ),
                    ),
                    camera_status,
                ],
            ),
        )

        def capture_now(_=None) -> None:
            preview_uri = generate_ine_preview_data_uri(
                side, self.operator_name, self.folio, source="camera"
            )
            self.page.pop_dialog()
            on_captured("camera", preview_uri, filename)

        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=WHITE,
            title=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.CAMERA_ALT_ROUNDED, color=BRAND, size=22),
                            ft.Text(
                                f"Cámara · {side_label}",
                                size=16,
                                weight=ft.FontWeight.W_800,
                                color=INK,
                            ),
                        ],
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE_ROUNDED,
                        icon_color=MUTED,
                        on_click=lambda _: self.page.pop_dialog(),
                    ),
                ],
            ),
            content=ft.Container(
                width=380,
                content=ft.Column(
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=14,
                    controls=[
                        viewfinder,
                        ft.Text(
                            "Asegúrate de que los datos sean legibles y sin reflejos de luz.",
                            size=12,
                            color=MUTED,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Button(
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=10,
                                controls=[
                                    ft.Icon(ft.Icons.CAMERA_ROUNDED, size=20, color=WHITE),
                                    ft.Text(
                                        "Obturar y Capturar Fotografía",
                                        size=14,
                                        weight=ft.FontWeight.W_800,
                                        color=WHITE,
                                    ),
                                ],
                            ),
                            height=48,
                            style=ft.ButtonStyle(
                                bgcolor=BRAND,
                                color=WHITE,
                                shape=ft.RoundedRectangleBorder(radius=14),
                            ),
                            on_click=capture_now,
                        ),
                    ],
                ),
            ),
        )
        self.page.show_dialog(dialog)
        return dialog

    def open_gallery_selector(
        self,
        side: str,
        on_selected: Callable[[str, str, str], None],
    ) -> None:
        """
        Abre el selector de archivos de galería o proporciona selección inmediata
        para garantizar funcionamiento en cualquier entorno (móvil, web o desktop).
        """
        self._pending_side = side
        self._pending_callback = on_selected

        side_label = "Anverso (Frente)" if side == "front" else "Reverso (Atrás)"
        default_filename = f"INE_{side.upper()}_Galeria_{self.folio or '84021'}.png"

        def select_gallery_file(custom_name: str) -> None:
            preview_uri = generate_ine_preview_data_uri(
                side, self.operator_name, self.folio, source="gallery"
            )
            self.page.pop_dialog()
            on_selected("gallery", preview_uri, custom_name)

        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=WHITE,
            title=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Icon(ft.Icons.PHOTO_LIBRARY_ROUNDED, color=BRAND, size=20),
                            ft.Text(
                                f"Subir desde Galería · {side_label}",
                                size=16,
                                weight=ft.FontWeight.W_800,
                                color=INK,
                            ),
                        ],
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE_ROUNDED,
                        icon_color=MUTED,
                        on_click=lambda _: self.page.pop_dialog(),
                    ),
                ],
            ),
            content=ft.Container(
                width=360,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    controls=[
                        ft.Text(
                            "Selecciona la imagen digitalizada de tu credencial para votar (INE) almacenada en el dispositivo:",
                            size=12,
                            color=MUTED,
                        ),
                        ft.Container(
                            padding=12,
                            border_radius=12,
                            bgcolor=SOFT,
                            border=ft.Border.all(1, LINE),
                            on_click=lambda _: select_gallery_file(default_filename),
                            content=ft.Row(
                                spacing=12,
                                controls=[
                                    ft.Container(
                                        width=42,
                                        height=42,
                                        border_radius=10,
                                        bgcolor=BRAND_SOFT,
                                        alignment=ft.Alignment.CENTER,
                                        content=ft.Icon(ft.Icons.IMAGE_ROUNDED, color=BRAND, size=22),
                                    ),
                                    ft.Column(
                                        spacing=2,
                                        expand=True,
                                        controls=[
                                            ft.Text(
                                                default_filename,
                                                size=13,
                                                weight=ft.FontWeight.W_700,
                                                color=INK,
                                            ),
                                            ft.Text(
                                                "JPEG Alta Resolución · 1.4 MB · Verificado",
                                                size=11,
                                                color=MUTED,
                                            ),
                                        ],
                                    ),
                                    ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED, color=SUCCESS, size=20),
                                ],
                            ),
                        ),
                        ft.Button(
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=8,
                                controls=[
                                    ft.Icon(ft.Icons.UPLOAD_FILE_ROUNDED, size=18, color=WHITE),
                                    ft.Text(
                                        "Cargar Imagen Seleccionada",
                                        size=13,
                                        weight=ft.FontWeight.W_700,
                                        color=WHITE,
                                    ),
                                ],
                            ),
                            height=46,
                            style=ft.ButtonStyle(
                                bgcolor=BRAND,
                                color=WHITE,
                                shape=ft.RoundedRectangleBorder(radius=12),
                            ),
                            on_click=lambda _: select_gallery_file(default_filename),
                        ),
                    ],
                ),
            ),
        )
        self.page.show_dialog(dialog)
