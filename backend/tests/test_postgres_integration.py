import os
import unittest
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg_pool import ConnectionPool

from backend.app import create_app
from backend.auth import hash_token
from backend.seed_routes import seed_l2


POSTGRES_URL = os.getenv("TEST_DATABASE_URL")
ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(POSTGRES_URL, "TEST_DATABASE_URL is required for integration tests")
class PostgresIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Never infer a test target from the API environment.
        from psycopg.conninfo import conninfo_to_dict

        if not conninfo_to_dict(POSTGRES_URL).get("dbname", "").endswith("_test"):
            raise RuntimeError("TEST_DATABASE_URL must name a disposable database ending in _test")
        with psycopg.connect(POSTGRES_URL, autocommit=True) as conn:
            schema = (ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
            with conn.cursor() as cur:
                cur.execute(schema, prepare=False)

        cls.pool = ConnectionPool(conninfo=POSTGRES_URL, min_size=1, max_size=4, open=True)
        cls.app = create_app(pool=cls.pool)
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.pool.close()

    def setUp(self):
        with psycopg.connect(POSTGRES_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    TRUNCATE TABLE
                        alerts,
                        telemetry,
                        vehicles,
                        devices,
                        route_stations,
                        stations,
                        routes
                    RESTART IDENTITY CASCADE;
                    """
                )
            conn.commit()
            seed_l2(conn)

            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO devices (device_id, name, token_hash) VALUES (%s, %s, %s);",
                    ("gps-01", "GPS Test", hash_token("gps-secret")),
                )
                cur.execute(
                    """
                    INSERT INTO vehicles (vehicle_id, display_name, route_id, device_id)
                    VALUES ('unit-01', 'Unidad Test', 'route-l2', 'gps-01');
                    """
                )
                cur.execute(
                    """
                    INSERT INTO alerts (
                        alert_id, route_id, type, message, severity, active
                    ) VALUES (
                        'alert-test', 'route-l2', 'service', 'Prueba de servicio', 'warning', TRUE
                    );
                    """
                )
            conn.commit()

    def telemetry_payload(self, seq=1):
        return {
            "schema_version": 1,
            "device_id": "gps-01",
            "vehicle_id": "unit-01",
            "seq": seq,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "position": {
                "lat": 19.6208198,
                "lon": -99.16778,
                "speed_mps": 7.0,
                "accuracy_m": 4.0,
                "heading_deg": 75.0,
                "satellites": 10,
            },
        }

    def test_end_to_end_api_database_cycle(self):
        ready = self.client.get("/v1/ready")
        self.assertEqual(ready.status_code, 200)
        self.assertEqual(ready.get_json()["database"], "ok")

        routes = self.client.get("/v1/routes").get_json()["routes"]
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0]["service_id"], "l2-ordinary")

        detail = self.client.get("/v1/routes/route-l2")
        self.assertEqual(detail.status_code, 200)
        self.assertGreater(len(detail.get_json()["path"]), 50)

        stations = self.client.get("/v1/routes/route-l2/stations").get_json()["stations"]
        self.assertEqual(len(stations), 43)
        self.assertEqual(stations[0]["order"], 1)
        self.assertEqual(stations[-1]["order"], 43)

        telemetry = self.client.post(
            "/v1/telemetry",
            json=self.telemetry_payload(),
            headers={"Authorization": "Device gps-secret"},
        )
        self.assertEqual(telemetry.status_code, 202)
        self.assertNotIn("duplicate", telemetry.get_json())

        duplicate = self.client.post(
            "/v1/telemetry",
            json=self.telemetry_payload(),
            headers={"Authorization": "Device gps-secret"},
        )
        self.assertEqual(duplicate.status_code, 202)
        self.assertTrue(duplicate.get_json()["duplicate"])

        vehicle = self.client.get("/v1/vehicles/unit-01")
        self.assertEqual(vehicle.status_code, 200)
        vehicle_json = vehicle.get_json()
        self.assertEqual(vehicle_json["status"], "online")
        self.assertIsNotNone(vehicle_json["navigation"])
        self.assertIn(vehicle_json["navigation"]["direction"], {"forward", "reverse"})
        self.assertIsNotNone(vehicle_json["navigation"]["eta_speed_mps"])

        alerts = self.client.get("/v1/alerts?route_id=route-l2")
        self.assertEqual(alerts.status_code, 200)
        self.assertEqual(alerts.get_json()["alerts"][0]["alert_id"], "alert-test")

        wrong_scheme = self.client.post(
            "/v1/telemetry",
            json=self.telemetry_payload(),
            headers={"Authorization": "Bearer not-device"},
        )
        self.assertEqual(wrong_scheme.status_code, 401)

    def test_real_http_simulator_to_frontend_adapters(self):
        import threading
        from unittest.mock import patch
        from werkzeug.serving import make_server
        from backend import dev_simulator as simulator
        from app.services import ApiAlertService, ApiVehicleService, load_route_from_api

        server = make_server("127.0.0.1", 0, self.app)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        base_url = f"http://127.0.0.1:{server.server_port}"
        try:
            with (
                patch.object(simulator, "POSTGRES_URL", POSTGRES_URL),
                patch.object(simulator, "API_BASE_URL", base_url),
                patch.object(simulator, "DEVICE_ID", "gps-demo-01"),
                patch.object(simulator, "VEHICLE_ID", "unit-demo-01"),
                patch.object(simulator, "ROUTE_ID", "route-l2"),
            ):
                seq = simulator.bootstrap_demo("integration-fixture-token")
                walker = simulator.RouteWalker(simulator.load_route_coordinates(), 1200)
                lat, lon, heading = walker.step(16)
                simulator.post_telemetry("integration-fixture-token", seq, lat, lon, heading)
                # A restart resumes sequence without erasing existing telemetry.
                self.assertEqual(simulator.bootstrap_demo("integration-fixture-token"), seq + 1)
            route = load_route_from_api(base_url, service_id="l2-ordinary")
            self.assertEqual(route.route_id, "route-l2")
            self.assertEqual(route.station_count, 43)
            adapter = ApiVehicleService(
                list(route.coordinates),
                base_url=base_url,
                vehicle_id="unit-demo-01",
                route_id=route.route_id,
                forward_direction_label=route.forward_label,
                reverse_direction_label=route.reverse_label,
            )
            snapshot = adapter._snapshot_from_payload(adapter._fetch_vehicle())
            self.assertTrue(snapshot.position_known)
            self.assertEqual(snapshot.status, "online")
            self.assertIsNotNone(snapshot.eta_seconds)
            self.assertTrue(snapshot.next_station_name)
            alert = ApiAlertService(
                base_url=base_url, route_id=route.route_id, vehicle_id="unit-demo-01"
            )._fetch_alerts()
            self.assertTrue(alert["active"])
        finally:
            server.shutdown()
            worker.join(timeout=5)
            server.server_close()


if __name__ == "__main__":
    unittest.main()
