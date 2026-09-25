import os
import unittest
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg_pool import ConnectionPool

from backend.API_Global import create_app
from backend.api_utils import hash_token
from backend.seed_routes import seed_l2


POSTGRES_URL = os.getenv("POSTGRES_URL")
ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(POSTGRES_URL, "POSTGRES_URL is required for integration tests")
class PostgresIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with psycopg.connect(POSTGRES_URL, autocommit=True) as conn:
            schema = (ROOT / "BD" / "database_v1.sql").read_text(encoding="utf-8")
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
                        incidents,
                        alerts,
                        telemetry,
                        driver_vehicle_assignments,
                        drivers,
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
                    "INSERT INTO drivers (driver_id, display_name, token_hash) VALUES (%s, %s, %s);",
                    ("driver-01", "Driver Test", hash_token("driver-secret")),
                )
                cur.execute(
                    """
                    INSERT INTO driver_vehicle_assignments (driver_id, vehicle_id)
                    VALUES ('driver-01', 'unit-01');
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
            "/v1/incidents",
            json={
                "vehicle_id": "unit-01",
                "type": "traffic",
                "description": "Prueba",
                "position": {"lat": 19.62, "lon": -99.16},
                "observed_at": datetime.now(timezone.utc).isoformat(),
            },
            headers={"Authorization": "Device gps-secret"},
        )
        self.assertEqual(wrong_scheme.status_code, 401)

        incident = self.client.post(
            "/v1/incidents",
            json={
                "vehicle_id": "unit-01",
                "type": "traffic",
                "description": "Prueba",
                "position": {"lat": 19.62, "lon": -99.16},
                "observed_at": datetime.now(timezone.utc).isoformat(),
            },
            headers={"Authorization": "Driver driver-secret"},
        )
        self.assertEqual(incident.status_code, 201)
        self.assertEqual(incident.get_json()["driver_id"], "driver-01")


if __name__ == "__main__":
    unittest.main()
