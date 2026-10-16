import os
import flet as ft

from app.models_driver import IneDocumentState, OperatorSession
from app.theme import configure
from app.views import passenger
from app.views.driver.ine_verification_view import IneVerificationView
from app.views.driver.login_view import DriverLoginView
from app.views.welcome_view import WelcomeView


class ZentryxUnifiedRouter:
    """
    Orquestador Universal de Zentryx (Python + Flet).
    Flujo unificado:
    - 'welcome': Interfaz de Inicio con opción 'Ver mapa y unidades' (Modo Pasajero)
      y opción extra 'Modo conductor'.
    - 'passenger': Interfaz de mapa y unidad en vivo (Modo Pasajero).
    - 'driver_login': Paso 1 de Verificación de Datos antes de acceder al Modo Conductor (Folio, Matrícula, QR).
    - 'driver_ine': Paso 2 de Verificación de Identidad (Captura INE Anverso/Reverso + Skeleton Loader).
    - 'driver_map' (alias 'driver_dashboard'): Redirige a la MISMA interfaz de mapa y datos de la unidad
      que el Modo Pasajero, integrando ahí mismo el apartado de Botón de Emergencia SOS y badge de operador.
    """

    def __init__(self, page: ft.Page, initial_mode: str | None = None):
        self.page = page
        configure(self.page)
        self.session = OperatorSession()
        self.current_route = initial_mode or os.getenv("ZENTRYX_INITIAL_MODE", "welcome")
        self.active_view = None
        self.active_panic_module = None

    def _clear_page(self) -> None:
        self.page.on_resize = None
        if hasattr(self.page, "controls") and isinstance(self.page.controls, list):
            self.page.controls.clear()
        elif hasattr(self.page, "clean"):
            self.page.clean()

    def navigate(self, route_name: str) -> None:
        self.current_route = route_name
        self._clear_page()

        if route_name == "welcome":
            view = WelcomeView(
                on_select_passenger=lambda: self.navigate("passenger"),
                on_select_driver=lambda: self.navigate("driver_login"),
            )
            self.active_view = view
            self.active_panic_module = None
            self.page.add(ft.SafeArea(content=view.control, expand=True))
            self.page.update()
            return

        if route_name == "passenger":
            self.active_view = None
            self.active_panic_module = None
            passenger.main(
                self.page,
                on_switch_driver=lambda: self.navigate("driver_login"),
                on_back_home=lambda: self.navigate("welcome"),
            )
            return

        if route_name == "driver_login":
            view = DriverLoginView(
                page=self.page,
                session=self.session,
                on_authenticated=lambda: self.navigate("driver_ine"),
                on_switch_passenger=lambda: self.navigate("welcome"),
            )
            self.active_view = view
            self.active_panic_module = None
            self.page.add(ft.SafeArea(content=view.control, expand=True))
            self.page.update()
            return

        if route_name == "driver_ine":
            view = IneVerificationView(
                page=self.page,
                session=self.session,
                on_verified=lambda: self.navigate("driver_map"),
                on_back_to_login=lambda: self.navigate("driver_login"),
                on_switch_passenger=lambda: self.navigate("welcome"),
            )
            self.active_view = view
            self.active_panic_module = None
            self.page.add(ft.SafeArea(content=view.control, expand=True))
            self.page.update()
            return

        if route_name in ("driver_map", "driver_dashboard"):
            self.active_view = None
            self.active_panic_module = passenger.main(
                self.page,
                driver_session=self.session,
                on_back_home=lambda: self.navigate("welcome"),
            )
            return

    def _reset_driver_session(self) -> None:
        self.session = OperatorSession(ine=IneDocumentState())
        self.navigate("welcome")


def launch_app(page: ft.Page) -> ZentryxUnifiedRouter:
    router = ZentryxUnifiedRouter(page)
    router.navigate(router.current_route)
    return router
