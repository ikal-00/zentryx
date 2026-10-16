import os
import flet as ft

from app.models_driver import IneDocumentState, OperatorSession
from app.theme import configure
from app.views import passenger
from app.views.driver.dashboard_view import DriverDashboardView
from app.views.driver.ine_verification_view import IneVerificationView
from app.views.driver.login_view import DriverLoginView


class ZentryxUnifiedRouter:
    """
    Orquestador Universal de Zentryx (100% Python + Flet).
    Gestiona la transición sin fricción entre:
    - 'passenger': Modo Pasajero (Mapa en vivo, telemetría y estaciones Mexibús L2).
    - 'driver_login': Paso 1 Modo Conductor (Folio Único, Matrícula y Escáner QR).
    - 'driver_ine': Paso 2 Modo Conductor (Captura de Anverso/Reverso INE con Cámara/Galería y Skeleton Loader).
    - 'driver_dashboard': Paso 3 Modo Conductor (Consola Operativa y Botón de Pánico SOS con fricción intencional).
    """

    def __init__(self, page: ft.Page, initial_mode: str | None = None):
        self.page = page
        configure(self.page)
        self.session = OperatorSession()
        self.current_route = initial_mode or os.getenv("ZENTRYX_INITIAL_MODE", "passenger")
        self.active_view = None

    def _clear_page(self) -> None:
        self.page.on_resize = None
        if hasattr(self.page, "controls") and isinstance(self.page.controls, list):
            self.page.controls.clear()
        elif hasattr(self.page, "clean"):
            self.page.clean()

    def navigate(self, route_name: str) -> None:
        self.current_route = route_name
        self._clear_page()

        if route_name == "passenger":
            self.active_view = None
            passenger.main(
                self.page,
                on_switch_driver=lambda: self.navigate("driver_login"),
            )
            return

        if route_name == "driver_login":
            view = DriverLoginView(
                page=self.page,
                session=self.session,
                on_authenticated=lambda: self.navigate("driver_ine"),
                on_switch_passenger=lambda: self.navigate("passenger"),
            )
            self.active_view = view
            self.page.add(ft.SafeArea(content=view.control, expand=True))
            self.page.update()
            return

        if route_name == "driver_ine":
            view = IneVerificationView(
                page=self.page,
                session=self.session,
                on_verified=lambda: self.navigate("driver_dashboard"),
                on_back_to_login=lambda: self.navigate("driver_login"),
                on_switch_passenger=lambda: self.navigate("passenger"),
            )
            self.active_view = view
            self.page.add(ft.SafeArea(content=view.control, expand=True))
            self.page.update()
            return

        if route_name == "driver_dashboard":
            view = DriverDashboardView(
                page=self.page,
                session=self.session,
                on_logout=self._reset_driver_session,
                on_switch_passenger=lambda: self.navigate("passenger"),
            )
            self.active_view = view
            self.page.add(ft.SafeArea(content=view.control, expand=True))
            self.page.update()
            return

    def _reset_driver_session(self) -> None:
        self.session = OperatorSession(ine=IneDocumentState())
        self.navigate("driver_login")


def launch_app(page: ft.Page) -> ZentryxUnifiedRouter:
    router = ZentryxUnifiedRouter(page)
    router.navigate(router.current_route)
    return router
