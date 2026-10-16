import unittest
import flet as ft
import flet_map as ftm

from app.router import ZentryxUnifiedRouter
from app.services.driver_service import simulate_qr_scan_payload
from app.views.driver.ine_verification_view import IneVerificationView
from app.views.driver.login_view import DriverLoginView
from app.views.welcome_view import WelcomeView


class DriverPageStub:
    def __init__(self):
        self.width = 430
        self.height = 932
        self.controls = []
        self.overlay = []
        self.services = []
        self.dialogs = []
        self.tasks = []
        self.updates = 0
        self.on_resize = None
        self.root = None

    def add(self, control):
        self.root = control
        self.controls.append(control)

    def clean(self):
        self.controls.clear()
        self.root = None

    def update(self):
        self.updates += 1

    def run_task(self, coro_fn):
        self.tasks.append(coro_fn)

    def show_dialog(self, dialog):
        self.dialogs.append(dialog)

    def pop_dialog(self):
        if self.dialogs:
            return self.dialogs.pop()
        return None


class DriverModeTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.page = DriverPageStub()
        self.router = ZentryxUnifiedRouter(self.page, initial_mode="welcome")
        self.router.navigate("welcome")

    def test_welcome_screen_has_passenger_and_driver_options(self):
        self.assertEqual(self.router.current_route, "welcome")
        self.assertIsInstance(self.router.active_view, WelcomeView)
        # Selecting driver option navigates to operator data verification (driver_login)
        self.router.active_view.on_select_driver()
        self.assertEqual(self.router.current_route, "driver_login")
        self.assertIsInstance(self.router.active_view, DriverLoginView)

    def test_operator_login_validation_and_animated_badge(self):
        self.router.navigate("driver_login")
        view = self.router.active_view
        self.assertIsInstance(view, DriverLoginView)

        self.assertEqual(view.auth_card.validation_container.opacity, 0.0)
        self.assertTrue(view.auth_card.continue_btn.disabled)

        view._handle_credentials_change("84", "123")
        self.assertEqual(view.auth_card.validation_container.opacity, 1.0)
        self.assertTrue(view.auth_card.continue_btn.disabled)

        view._handle_credentials_change("84021", "mex1234")
        self.assertTrue(self.router.session.is_valid_assignment)
        self.assertEqual(self.router.session.unit_plate, "MEX-1234")
        self.assertEqual(
            view.auth_card.status_title.value,
            "Operador Vigente y Asignado",
        )
        self.assertFalse(view.auth_card.continue_btn.disabled)

    def test_qr_scanner_modal_autofills_and_validates_operator(self):
        self.router.navigate("driver_login")
        view = self.router.active_view
        view._handle_open_qr()
        self.assertEqual(len(self.page.dialogs), 1)

        folio, plate, token = simulate_qr_scan_payload(0)
        view._on_qr_verified(folio, plate, token)

        self.assertTrue(self.router.session.is_valid_assignment)
        self.assertEqual(self.router.session.folio, "84021")
        self.assertEqual(self.router.session.unit_plate, "MEX-1234")
        self.assertEqual(self.router.session.auth_method, "qr")

        view._handle_submit()
        self.assertEqual(self.router.current_route, "driver_ine")
        self.assertIsInstance(self.router.active_view, IneVerificationView)

    async def test_ine_verification_redirects_to_shared_passenger_map_with_panic_button(self):
        self.router.session.folio = "84021"
        self.router.session.unit_plate = "MEX-1234"
        self.router.session.operator_name = "Carlos Eduardo Mendoza Rojas"
        self.router.navigate("driver_ine")

        ine_view = self.router.active_view
        self.assertIsInstance(ine_view, IneVerificationView)
        self.assertTrue(ine_view.verify_btn.disabled)

        ine_view.record_capture(
            "front",
            "camera",
            "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4=",
            "INE_FRONT_84021_CAM.jpg",
        )
        ine_view.record_capture(
            "back",
            "gallery",
            "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4=",
            "INE_BACK_Galeria_84021.png",
        )
        self.assertFalse(ine_view.verify_btn.disabled)

        ine_view.start_verification()
        self.assertTrue(self.router.session.ine.verifying)
        self.assertTrue(ine_view.skeleton_loader.control.visible)

        await self.page.tasks[-1]()
        self.assertTrue(self.router.session.ine.verified)
        self.assertEqual(self.router.current_route, "driver_map")
        self.assertIsNotNone(self.router.active_panic_module)

    async def test_panic_button_on_shared_map_interface(self):
        self.router.session.folio = "84021"
        self.router.session.unit_plate = "MEX-1234"
        self.router.session.operator_name = "Carlos Eduardo Mendoza Rojas"
        self.router.navigate("driver_map")

        panic = self.router.active_panic_module
        self.assertIsNotNone(panic)

        # Single accidental tap does NOT trigger alert
        panic._on_accidental_single_tap()
        self.assertFalse(panic.persistent_alert_banner.visible)

        # Early release (< 3s) cancels countdown
        panic.HOLD_DURATION_SECONDS = 0.15
        panic.TICK_SECONDS = 0.05
        panic._on_hold_start()
        panic._on_hold_end()
        self.assertFalse(panic.persistent_alert_banner.visible)
        self.assertEqual(panic.main_ring.value, 0.0)

        # Full 3s hold dispatches live unit GPS coordinates to Central
        panic._on_hold_start()
        await self.page.tasks[-1]()
        self.assertTrue(panic.persistent_alert_banner.visible)
        self.assertEqual(self.router.session.last_alert.trigger_method, "hold_3s")

        # Slide-to-confirm at 100% also dispatches
        panic._dismiss_banner()
        panic.confirm_slider.value = 100
        panic._on_slider_release(None)
        self.assertTrue(panic.persistent_alert_banner.visible)
        self.assertEqual(self.router.session.last_alert.trigger_method, "slide_confirm")


if __name__ == "__main__":
    unittest.main()
