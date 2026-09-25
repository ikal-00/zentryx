import unittest
from datetime import datetime, timedelta, timezone

from backend.API_Global import create_app
from backend.api_utils import (
    PayloadValidationError,
    hash_device_token,
    parse_driver_authorization,
    validate_telemetry_payload,
    verify_device_token,
)
from backend.navigation import RouteNavigator


class DummyPool:
    pass


class ApiContractTests(unittest.TestCase):
    def test_url_map_matches_v1_contract(self):
        app = create_app(pool=DummyPool())
        rules = {rule.rule for rule in app.url_map.iter_rules()}
        expected = {
            "/v1/health",
            "/v1/ready",
            "/v1/routes",
            "/v1/routes/<string:route_id>",
            "/v1/routes/<string:route_id>/stations",
            "/v1/stations",
            "/v1/vehicles",
            "/v1/vehicles/<string:vehicle_id>",
            "/v1/telemetry",
            "/v1/alerts",
            "/v1/incidents",
        }
        self.assertTrue(expected.issubset(rules))

    def test_health_does_not_require_database(self):
        app = create_app(pool=DummyPool())
        response = app.test_client().get("/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})

    def test_telemetry_validation_normalizes_contract_fields(self):
        now = datetime.now(timezone.utc)
        payload = validate_telemetry_payload(
            {
                "schema_version": 1,
                "device_id": "gps-01",
                "vehicle_id": "unit-01",
                "seq": 9,
                "observed_at": now.isoformat(),
                "position": {
                    "lat": 19.62211,
                    "lon": -99.16299,
                    "speed_mps": 8.3,
                    "accuracy_m": 4.7,
                    "heading_deg": 124.5,
                    "satellites": 12,
                },
            },
            now=now,
        )
        self.assertEqual(payload["position"]["speed_mps"], 8.3)
        self.assertEqual(payload["position"]["heading_deg"], 124.5)
        self.assertTrue(payload["observed_at"].endswith("Z"))

    def test_telemetry_rejects_clock_skew(self):
        now = datetime.now(timezone.utc)
        base = {
            "schema_version": 1,
            "device_id": "gps-01",
            "vehicle_id": "unit-01",
            "seq": 1,
            "position": {"lat": 19.6, "lon": -99.1},
        }
        with self.assertRaises(PayloadValidationError):
            validate_telemetry_payload(
                {**base, "observed_at": (now + timedelta(minutes=6)).isoformat()},
                now=now,
            )
        with self.assertRaises(PayloadValidationError):
            validate_telemetry_payload(
                {**base, "observed_at": (now - timedelta(hours=25)).isoformat()},
                now=now,
            )

    def test_invalid_coordinate_is_422_candidate(self):
        now = datetime.now(timezone.utc)
        with self.assertRaises(PayloadValidationError):
            validate_telemetry_payload(
                {
                    "schema_version": 1,
                    "device_id": "gps-01",
                    "vehicle_id": "unit-01",
                    "seq": 1,
                    "observed_at": now.isoformat(),
                    "position": {"lat": 100, "lon": -99},
                },
                now=now,
            )

    def test_device_token_is_hashed_not_plaintext(self):
        token = "development-device-token"
        stored = hash_device_token(token)
        self.assertTrue(stored.startswith("sha256:"))
        self.assertNotIn(token, stored)
        self.assertTrue(verify_device_token(stored, token))
        self.assertFalse(verify_device_token(stored, "wrong-token"))

    def test_driver_authorization_uses_separate_scheme(self):
        self.assertEqual(parse_driver_authorization("Driver abc"), "abc")
        with self.assertRaises(PayloadValidationError):
            parse_driver_authorization("Device abc")

    def test_navigation_uses_history_and_keeps_eta_when_stopped(self):
        route = [(19.0, -99.0), (19.0, -98.99)]
        stations = [
            {"station_id": "a", "name": "A", "stop_order": 1, "lat": 19.0, "lon": -99.0},
            {"station_id": "b", "name": "B", "stop_order": 2, "lat": 19.0, "lon": -98.99},
        ]
        navigator = RouteNavigator(route, stations)
        result = navigator.navigation(
            lat=19.0,
            lon=-98.995,
            history=[{"lat": 19.0, "lon": -98.996}],
            heading_deg=90,
            speed_mps=0.0,
            smoothed_speed_mps=4.0,
            default_speed_mps=6.0,
        )
        self.assertEqual(result.direction, 1)
        self.assertEqual(result.direction_source, "history")
        self.assertEqual(result.next_station_id, "b")
        self.assertGreater(result.distance_remaining_m, 0)
        self.assertGreater(result.eta_seconds, 0)
        self.assertEqual(result.eta_speed_mps, 4.0)

    def test_navigation_can_infer_direction_from_heading(self):
        navigator = RouteNavigator(
            [(19.0, -99.0), (19.0, -98.99)],
            [
                {"station_id": "a", "name": "A", "stop_order": 1, "lat": 19.0, "lon": -99.0},
                {"station_id": "b", "name": "B", "stop_order": 2, "lat": 19.0, "lon": -98.99},
            ],
        )
        result = navigator.navigation(
            lat=19.0,
            lon=-98.995,
            history=[],
            heading_deg=90,
            speed_mps=0,
            smoothed_speed_mps=0,
            default_speed_mps=6,
        )
        self.assertEqual(result.direction, 1)
        self.assertEqual(result.direction_source, "heading")
        self.assertEqual(result.eta_speed_mps, 6.0)


if __name__ == "__main__":
    unittest.main()
