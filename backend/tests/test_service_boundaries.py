"""Regression coverage for extracted write services and HTTP error mappings."""

import unittest
from unittest.mock import patch

from backend.app import create_app
from backend.services import telemetry
from backend.services.errors import AssignmentNotFound, AuthenticationError
from backend.services.simulation import RouteWalker


class ServiceBoundaryTests(unittest.TestCase):
    def test_duplicate_telemetry_acknowledgement_and_authorization(self):
        payload = {"device_id": "gps-test", "vehicle_id": "unit-test", "seq": 7}
        with (
            patch.object(telemetry, "authenticate_vehicle_device", return_value=("gps-test", None)),
            patch.object(telemetry.repository, "insert_telemetry", return_value=False),
        ):
            self.assertEqual(
                telemetry.accept_telemetry(object(), payload, "fixture"),
                {
                    "accepted": True,
                    "device_id": "gps-test",
                    "seq": 7,
                    "duplicate": True,
                },
            )
        with (
            patch.object(
                telemetry,
                "authenticate_vehicle_device",
                return_value=(None, "invalid_authorization"),
            ),
            patch.object(telemetry.repository, "insert_telemetry") as write,
        ):
            with self.assertRaises(AuthenticationError):
                telemetry.accept_telemetry(object(), payload, "fixture")
            write.assert_not_called()

    def test_service_errors_keep_http_status_and_json(self):
        app = create_app(pool=object())
        for error, status in [
            (AuthenticationError("invalid_authorization"), 401),
            (AssignmentNotFound("device_or_vehicle_not_found"), 404),
        ]:
            with patch("backend.routes.vehicles.vehicles.get_vehicle", side_effect=error):
                result = app.test_client().get("/v1/vehicles/missing")
                self.assertEqual(result.status_code, status)
                self.assertEqual(result.get_json(), {"error": str(error)})

    def test_simulator_turns_at_both_terminals(self):
        walker = RouteWalker([(19.0, -99.0), (19.0, -98.99)], 0)
        walker.step(walker.total_length_m + 10)
        self.assertEqual(walker.direction, -1)
        self.assertAlmostEqual(walker.progress_m, walker.total_length_m - 10)
        walker.step(walker.total_length_m)
        self.assertEqual(walker.direction, 1)
        self.assertAlmostEqual(walker.progress_m, 10)
