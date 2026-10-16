import asyncio
from datetime import datetime
from typing import Callable
import flet as ft

from app.components.camera_handler import CameraCaptureHandler
from app.components.driver.ine_capture_card import (
    IneCaptureSideCard,
    IneVerificationSkeletonLoader,
)
from app.models_driver import OperatorSession
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


class IneVerificationView:
    """
    Vista 2 del Modo Conductor: Flujo de Verificación de Identidad (Captura de INE).
    - Instrucción clara: 'Toma una foto del anverso y reverso de tu INE'.
    - Integración de Cámara en Flet + Previsualización + Botón de respaldo 'Subir desde Galería'.
    - Estado de Procesamiento asíncrono con Skeleton Loader sin congelar la app.
    """

    def __init__(
        self,
        page: ft.Page,
        session: OperatorSession,
        on_verified: Callable[[], None],
        on_back_to_login: Callable[[], None],
        on_switch_passenger: Callable[[], None],
    ):
        self.page = page
        self.session = session
        self.on_verified = on_verified
        self.on_back_to_login = on_back_to_login
        self.on_switch_passenger = on_switch_passenger

        self.camera_handler = CameraCaptureHandler(
            page=self.page,
            operator_name=self.session.operator_name,
            folio=self.session.folio,
        )

        self.front_card = IneCaptureSideCard(
            side="front",
            title="Anverso de tu INE (Frente)",
            subtitle="Fotografía clara mostrando rostro, nombre completo y clave de elector",
            on_camera_click=self._handle_camera_capture,
            on_gallery_click=self._handle_gallery_upload,
        )

        self.back_card = IneCaptureSideCard(
            side="back",
            title="Reverso de tu INE (Atrás)",
            subtitle="Fotografía clara mostrando códigos QR oficiales, huella y zona MRZ (CIC)",
            on_camera_click=self._handle_camera_capture,
            on_gallery_click=self._handle_gallery_upload,
        )

        self.skeleton_loader = IneVerificationSkeletonLoader()

        self.verify_btn = ft.Button(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.VERIFIED_USER_ROUNDED, size=18, color=WHITE),
                    ft.Text(
                        "Verificar Identidad e Iniciar Turno",
                        size=14,
                        weight=ft.FontWeight.W_800,
                        color=WHITE,
                    ),
                ],
            ),
            height=52,
            disabled=not self.session.ine.ready_for_verification,
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
            on_click=lambda _: self.start_verification(),
        )

        self.control = self._build()
        self.sync_ui()

    def _handle_camera_capture(self, side: str) -> None:
        self.camera_handler.operator_name = self.session.operator_name
        self.camera_handler.folio = self.session.folio
        self.camera_handler.open_camera_modal(
            side=side,
            on_captured=lambda source, uri, fname: self.record_capture(side, source, uri, fname),
        )

    def _handle_gallery_upload(self, side: str) -> None:
        self.camera_handler.operator_name = self.session.operator_name
        self.camera_handler.folio = self.session.folio
        self.camera_handler.open_gallery_selector(
            side=side,
            on_selected=lambda source, uri, fname: self.record_capture(side, source, uri, fname),
        )

    def record_capture(self, side: str, source: str, preview_uri: str, filename: str) -> None:
        ine = self.session.ine
        if side == "front":
            ine.front_captured = True
            ine.front_source = source
            ine.front_preview_uri = preview_uri
            ine.front_filename = filename
        else:
            ine.back_captured = True
            ine.back_source = source
            ine.back_preview_uri = preview_uri
            ine.back_filename = filename

        self.sync_ui()
        self.page.update()

    def sync_ui(self) -> None:
        ine = self.session.ine
        self.front_card.sync(
            captured=ine.front_captured,
            source=ine.front_source,
            preview_uri=ine.front_preview_uri,
            filename=ine.front_filename,
        )
        self.back_card.sync(
            captured=ine.back_captured,
            source=ine.back_source,
            preview_uri=ine.back_preview_uri,
            filename=ine.back_filename,
        )
        self.skeleton_loader.sync(ine)
        self.verify_btn.disabled = (not ine.ready_for_verification) or ine.verifying

    def start_verification(self) -> None:
        if not self.session.ine.ready_for_verification or self.session.ine.verifying:
            return
        self.session.ine.verifying = True
        self.session.ine.verification_progress = 0.1
        self.session.ine.verification_step_label = "Extrayendo biometría y hologramas del anverso..."
        self.sync_ui()
        self.page.update()
        self.page.run_task(self._run_async_verification)

    async def _run_async_verification(self) -> None:
        steps = [
            (0.35, "Validando zona de lectura mecánica (MRZ) y código CIC en reverso..."),
            (0.70, "Cotejando identidad con padrón estatal SITRAMYTEM / Mexibús L2..."),
            (1.00, "✓ Identidad verificada con éxito. Habilitando consola de unidad..."),
        ]
        for progress, label in steps:
            await asyncio.sleep(0.35)
            self.session.ine.verification_progress = progress
            self.session.ine.verification_step_label = label
            self.sync_ui()
            self.page.update()

        await asyncio.sleep(0.2)
        self.session.ine.verifying = False
        self.session.ine.verified = True
        self.session.ine.verified_at = datetime.now().strftime("%H:%M:%S")
        self.session.active_shift = True
        self.sync_ui()
        self.page.update()
        self.on_verified()

    def _build(self) -> ft.Container:
        header = ft.Container(
            padding=ft.Padding.symmetric(horizontal=20, vertical=14),
            bgcolor=INK,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK_ROUNDED,
                                icon_color=WHITE,
                                tooltip="Volver al Login de Operador",
                                on_click=lambda _: self.on_back_to_login(),
                            ),
                            ft.Column(
                                spacing=1,
                                controls=[
                                    ft.Text(
                                        "VERIFICACIÓN DE IDENTIDAD (INE)",
                                        size=13,
                                        weight=ft.FontWeight.W_800,
                                        color=WHITE,
                                    ),
                                    ft.Text(
                                        f"Operador #{self.session.folio} · Unidad {self.session.unit_plate}",
                                        size=11,
                                        color="#9CA3AF",
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.OutlinedButton(
                        content=ft.Text("Modo Pasajero", size=12, weight=ft.FontWeight.W_700, color=WHITE),
                        style=ft.ButtonStyle(
                            side=ft.BorderSide(1, "#374151"),
                            shape=ft.RoundedRectangleBorder(radius=999),
                        ),
                        on_click=lambda _: self.on_switch_passenger(),
                    ),
                ],
            ),
        )

        instruction_banner = ft.Container(
            width=480,
            padding=20,
            border_radius=18,
            bgcolor=WHITE,
            border=ft.Border.all(1, LINE),
            shadow=shadow(),
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.Container(
                                width=38,
                                height=38,
                                border_radius=10,
                                bgcolor=BRAND_SOFT,
                                alignment=ft.Alignment.CENTER,
                                content=ft.Icon(ft.Icons.ASSIGNMENT_IND_ROUNDED, color=BRAND, size=20),
                            ),
                            ft.Column(
                                spacing=2,
                                expand=True,
                                controls=[
                                    ft.Text(
                                        "PASO 2 DE 3 · SEGURIDAD BIOMÉTRICA",
                                        size=10,
                                        weight=ft.FontWeight.W_800,
                                        color=BRAND,
                                    ),
                                    ft.Text(
                                        "Toma una foto del anverso y reverso de tu INE",
                                        size=17,
                                        weight=ft.FontWeight.W_800,
                                        color=INK,
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.Text(
                        "Por protocolo de seguridad del corredor Mexibús Línea 2, verifica tu identidad antes de liberar los controles de la unidad.",
                        size=12,
                        color=MUTED,
                    ),
                ],
            ),
        )

        cards_wrapper = ft.Container(
            width=480,
            content=ft.Column(
                spacing=14,
                controls=[
                    self.front_card.control,
                    self.back_card.control,
                    self.skeleton_loader.control,
                    self.verify_btn,
                ],
            ),
        )

        return ft.Container(
            expand=True,
            bgcolor=PAPER,
            content=ft.Column(
                expand=True,
                spacing=0,
                controls=[
                    header,
                    ft.Container(
                        expand=True,
                        padding=20,
                        alignment=ft.Alignment.TOP_CENTER,
                        content=ft.Column(
                            scroll=ft.ScrollMode.AUTO,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=14,
                            controls=[
                                instruction_banner,
                                cards_wrapper,
                            ],
                        ),
                    ),
                ],
            ),
        )
