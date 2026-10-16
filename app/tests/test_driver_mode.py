import asyncio
import unittest
import flet as ft

from app.router import ZentryxUnifiedRouter
from app.services.driver_service import (
    normalize_plate,
    simulate_qr_scan_payload,
    validate_operator_credentials,
)
from app.views.driver.dashboard_view import DriverDashboardView
from app.views.driver.ine_verification_view import IneVerificationView
from app.views.driver.login_view import DriverLoginView


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
        self.router = ZentryxUnifiedRouter(self.page, initial_mode="driver_login")
        self.router.navigate("driver_login")

    def test_operator_login_validation_and_animated_badge(self):
        view = self.router.active_view
        self.assertIsInstance(view, DriverLoginView)

        # Initially empty -> opacity 0.0 and continue button disabled
        self.assertEqual(view.auth_card.validation_container.opacity, 0.0)
        self.assertTrue(view.auth_card.continue_btn.disabled)

        # Partial/invalid input -> shows pending warning, button still disabled
        view._handle_credentials_change("84", "123")
        self.assertEqual(view.auth_card.validation_container.opacity, 1.0)
        self.assertTrue(view.auth_card.continue_btn.disabled)

        # Valid Folio and Plate -> shows 'Operador Vigente y Asignado' and enables button
        view._handle_credentials_change("84021", "mex1234")
        self.assertTrue(self.router.session.is_valid_assignment)
        self.assertEqual(self.router.session.unit_plate, "MEX-1234")
        self.assertEqual(
            view.auth_card.status_title.value,
            "Operador Vigente y Asignado",
        )
        self.assertFalse(view.auth_card.continue_btn.disabled)

    def test_qr_scanner_modal_autofills_and_validates_operator(self):
        view = self.router.active_view
        view._handle_open_qr()
        self.assertEqual(len(self.page.dialogs), 1)

        folio, plate, token = simulate_qr_scan_payload(0)
        view._on_qr_verified(folio, plate, token)

        self.assertTrue(self.router.session.is_valid_assignment)
        self.assertEqual(self.router.session.folio, "84021")
        self.assertEqual(self.router.session.unit_plate, "MEX-1234")
        self.assertEqual(self.router.session.auth_method, "qr")

        # Submitting transitions router to Step 2 (INE Verification)
        view._handle_submit()
        self.assertEqual(self.router.current_route, "driver_ine")
        self.assertIsInstance(self.router.active_view, IneVerificationView)

    async def test_ine_capture_camera_gallery_and_async_skeleton_verification(self):
        self.router.session.folio = "84021"
        self.router.session.unit_plate = "MEX-1234"
        self.router.session.operator_name = "Carlos Eduardo Mendoza Rojas"
        self.router.navigate("driver_ine")

        ine_view = self.router.active_view
        self.assertIsInstance(ine_view, IneVerificationView)
        self.assertTrue(ine_view.verify_btn.disabled)

        # 1. Capture Front via Camera modal
        ine_view._handle_camera_capture("front")
        self.assertEqual(len(self.page.dialogs), 1)
        # Simulate shutter click callback
        ine_view.record_capture(
            "front",
            "camera",
            "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4=",
            "INE_FRONT_84021_CAM.jpg",
        )
        self.assertTrue( self.router.session.ine.front_captured)
        self.assertTrue(ine_view.front_card.preview_image.visible)
        self.assertTrue(ine_view.verify_btn.disabled)  # Back still pending

        # 2. Capture Back via Backup 'Subir desde Galería'
        ine_view._handle_gallery_upload("back")
        ine_view.record_capture(
            "back",
            "gallery",
            "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4=",
            "INE_BACK_Galeria_84021.png",
        )
        self.assertTrue(self.router.session.ine.back_captured)
        self.assertTrue(ine_view.back_card.preview_image.visible)
        self.assertFalse(ine_view.verify_btn.disabled)

        # 3. Start non-blocking verification with Skeleton Loader
        ine_view.start_verification()
        self.assertTrue(self.router.session.ine.verifying)
        self.assertTrue(ine_view.skeleton_loader.control.visible)
        self.assertEqual(len(self.page.tasks), 1)

        # Execute the async verification coroutine
        await self.page.tasks[-1]()
        self.assertTrue(self.router.session.ine.verified)
        self.assertFalse(self.router.session.ine.verifying)
        self.assertEqual(self.router.current_route, "driver_dashboard")
        self.assertIsInstance(self.router.active_view, DriverDashboardView)

    async def test_panic_button_intentional_friction_and_alert_dispatch(self):
        self.router.session.folio = "84021"
        self.router.session.unit_plate = "MEX-1234"
        self.router.session.operator_name = "Carlos Eduardo Mendoza Rojas"
        self.router.navigate("driver_dashboard")

        dash = self.router.active_view
        self.assertIsInstance(dash, DriverDashboardView)
        panic = dash.panic_module

        # 1. Accidental single tap MUST NOT trigger the alert
        panic._on_accidental_single_tap()
        self.assertFalse(panic.persistent_alert_banner.visible)
        self.assertIsNone(self.router.session.last_alert)

        # 2. Hold started and released early (< 3s) MUST cancel and reset ring to 0.0
        panic.HOLD_DURATION_SECONDS = 0.15
        panic.TICK_SECONDS = 0.05
        panic._on_hold_start()
        panic._on_hold_end()
        self.assertFalse(panic.persistent_alert_banner.visible)
        self.assertEqual(panic.main_ring.value, 0.0)

        # 3. Full 3-second hold completes and dispatches coordinates to Central
        panic._on_hold_start()
        await self.page.tasks[-1]()
        self.assertTrue(panic.persistent_alert_banner.visible)
        self.assertIsNotNone(self.router.session.last_alert)
        self.assertEqual(self.router.session.last_alert.trigger_method, "hold_3s")
        self.assertIn(
            "Alerta enviada a Central con coordenadas actuales",
            panic.banner_title.value,
        )

        # 4. Dismiss banner and test Slide-to-confirm friction (partial slide vs 100% slide)
        panic._dismiss_banner()
        self.assertFalse(panic.persistent_alert_banner.visible)

        panic.confirm_slider.value = 50
        panic._on_slider_release(None)
        self.assertFalse(panic.persistent_alert_banner.visible)
        self.assertEqual(panic.confirm_slider.value, 0)

        panic.confirm_slider.value = 100
        panic._on_slider_release(None)
        self.assertTrue(panic.persistent_alert_banner.visible)
        self.assertEqual(self.router.session.last_alert.trigger_method, "slide_confirm")

    def test_mode_switch_between_passenger_and_driver(self):
        self.router.navigate("passenger")
        self.assertEqual(self.router.current_route, "passenger")
        self.assertIsNotNone(self.page.root)

        self.router.navigate("driver_login")
        self.assertEqual(self.router.current_route, "driver_login")
        self.assertIsInstance(self.router.active_view, DriverLoginView)


if __name__ == "__main__":
    unittest.main()
