import unittest
from unittest.mock import patch

from services import ApiAlertService, ApiVehicleService, load_route, load_route_from_api


class ApiAdapterTests(unittest.TestCase):
    def setUp(self):
        self.route = load_route("l2-ordinary")

    def test_vehicle_unknown_direction_is_not_forced_forward(self):
        service = ApiVehicleService(
            list(self.route.coordinates),
            base_url="http://api.test",
            vehicle_id="unit-01",
            route_id=self.route.route_id,
            forward_direction_label=self.route.forward_label,
            reverse_direction_label=self.route.reverse_label,
        )
        snapshot = service._snapshot_from_payload(
            {
                "vehicle_id": "unit-01",
                "route_id": self.route.route_id,
                "status": "online",
                "position": {"lat": 19.62, "lon": -99.16},
                "speed_mps": 0,
                "heading_deg": None,
                "occupancy_level": "unknown",
                "navigation": {
                    "direction": "unknown",
                    "direction_label": None,
                    "progress_m": 100,
                    "route_length_m": 20000,
                    "next_station": None,
                    "eta_seconds": None,
                },
            }
        )
        self.assertEqual(snapshot.direction, 0)
        self.assertEqual(snapshot.direction_label, "Dirección por determinar")

    def test_initial_api_failure_snapshot_has_no_fake_position(self):
        service = ApiVehicleService(
            list(self.route.coordinates),
            base_url="http://api.test",
            vehicle_id="unit-01",
            route_id=self.route.route_id,
            forward_direction_label=self.route.forward_label,
            reverse_direction_label=self.route.reverse_label,
        )
        snapshot = service._offline_snapshot()
        self.assertFalse(snapshot.position_known)
        self.assertEqual(snapshot.status, "offline")
        self.assertEqual(snapshot.direction, 0)

    def test_route_can_be_built_from_api_contract(self):
        routes_payload = {
            "routes": [
                {
                    "route_id": "route-l2",
                    "service_id": "l2-ordinary",
                }
            ]
        }
        detail = {
            "route_id": "route-l2",
            "line_id": "mexibus-l2",
            "line_label": "L2",
            "network_name": "Mexibús",
            "service_id": "l2-ordinary",
            "service_name": "Servicio ordinario",
            "origin_name": "A",
            "destination_name": "B",
            "direction_forward_label": "A → B",
            "direction_reverse_label": "B → A",
            "path": [
                {"lat": 19.0, "lon": -99.0},
                {"lat": 19.1, "lon": -99.1},
            ],
        }
        stations = {
            "route_id": "route-l2",
            "stations": [
                {
                    "station_id": "a",
                    "name": "A",
                    "position": {"lat": 19.0, "lon": -99.0},
                    "order": 1,
                },
                {
                    "station_id": "b",
                    "name": "B",
                    "position": {"lat": 19.1, "lon": -99.1},
                    "order": 2,
                },
            ],
        }
        with patch(
            "services.api_route_service._get_json",
            side_effect=[routes_payload, detail, stations],
        ):
            route = load_route_from_api(
                "http://api.test",
                service_id="l2-ordinary",
            )
        self.assertEqual(route.service_id, "l2-ordinary")
        self.assertEqual(route.station_count, 2)
        self.assertEqual(route.coordinates[1], (19.1, -99.1))

    def test_alert_service_selects_first_server_priority_alert(self):
        service = ApiAlertService(
            base_url="http://api.test",
            route_id="route-l2",
            vehicle_id="unit-01",
        )
        payload = {
            "alerts": [
                {
                    "alert_id": "critical-1",
                    "severity": "critical",
                    "message": "Test",
                    "active": True,
                }
            ]
        }

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                import json

                return json.dumps(payload).encode("utf-8")

        with patch("services.api_alert_service.urlopen", return_value=Response()):
            alert = service._fetch_alerts()
        self.assertEqual(alert["alert_id"], "critical-1")


if __name__ == "__main__":
    unittest.main()
