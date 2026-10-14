#!/usr/bin/env python3
"""Zentryx Local Mock API Server with Real-Time Bus Telemetry Simulation.

Runs with ZERO external dependencies (pure Python 3 standard library).
Provides all API v1 endpoints with CORS enabled, ideal for testing Flutter
(web, desktop, or mobile) locally on macOS without needing Docker or PostgreSQL.
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
ROUTES_DIR = ROOT / "app" / "assets" / "routes"
ROUTE_GEOJSON = ROUTES_DIR / "l2_ordinary_route.geojson"
STATIONS_GEOJSON = ROUTES_DIR / "l2_ordinary_stations.geojson"

PORT = int(os.getenv("PORT", "5050"))
HOST = os.getenv("HOST", "0.0.0.0")


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    )
    return 2.0 * r * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    y = math.sin(dlambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


class RouteSimulation:
    def __init__(self):
        # 1. Load Route Path
        route_raw = json.loads(ROUTE_GEOJSON.read_text(encoding="utf-8"))
        features = route_raw.get("features", [])
        line_feature = next(f for f in features if f.get("geometry", {}).get("type") == "LineString")
        coords = line_feature["geometry"]["coordinates"]
        self.path_points = [{"lat": float(lat), "lon": float(lon)} for lon, lat in coords]

        # 2. Compute cumulative distances along path
        self.segments: list[float] = []
        self.cumulative_dist: list[float] = [0.0]
        for i in range(len(self.path_points) - 1):
            p1 = self.path_points[i]
            p2 = self.path_points[i + 1]
            d = haversine_m(p1["lat"], p1["lon"], p2["lat"], p2["lon"])
            self.segments.append(d)
            self.cumulative_dist.append(self.cumulative_dist[-1] + d)
        self.total_length_m = self.cumulative_dist[-1]

        # 3. Load Stations
        stations_raw = json.loads(STATIONS_GEOJSON.read_text(encoding="utf-8"))
        self.stations: list[dict] = []
        for feat in stations_raw.get("features", []):
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})
            lon, lat = geom.get("coordinates", [0.0, 0.0])
            self.stations.append({
                "station_id": str(props.get("station_id") or props.get("id") or f"st-{len(self.stations)+1}"),
                "name": str(props.get("name", "Estación")),
                "position": {"lat": float(lat), "lon": float(lon)},
                "order": int(props.get("order", len(self.stations) + 1)),
                "active": True,
            })
        self.stations.sort(key=lambda s: s["order"])

        self.start_time = time.time()
        self.speed_mps = 8.0

    def get_vehicle_state(self) -> dict:
        elapsed = time.time() - self.start_time
        dist = (elapsed * self.speed_mps) % (self.total_length_m * 2)

        # Forward or Reverse direction loop
        if dist <= self.total_length_m:
            direction = "forward"
            direction_label = "La Quebrada → Las Américas"
            curr_dist = dist
        else:
            direction = "reverse"
            direction_label = "Las Américas → La Quebrada"
            curr_dist = self.total_length_m - (dist - self.total_length_m)

        # Find current segment
        idx = 0
        while idx < len(self.cumulative_dist) - 2 and self.cumulative_dist[idx + 1] < curr_dist:
            idx += 1

        seg_start = self.cumulative_dist[idx]
        seg_len = self.segments[idx] if idx < len(self.segments) else 1.0
        frac = min(1.0, max(0.0, (curr_dist - seg_start) / seg_len)) if seg_len > 0 else 0.0

        p1 = self.path_points[idx]
        p2 = self.path_points[min(idx + 1, len(self.path_points) - 1)]

        cur_lat = p1["lat"] + frac * (p2["lat"] - p1["lat"])
        cur_lon = p1["lon"] + frac * (p2["lon"] - p1["lon"])
        heading = bearing_deg(p1["lat"], p1["lon"], p2["lat"], p2["lon"])
        if direction == "reverse":
            heading = (heading + 180.0) % 360.0

        # Find next station along direction
        if direction == "forward":
            next_st = self.stations[-1]
            dist_to_st = 300.0
            for st in self.stations:
                d = haversine_m(cur_lat, cur_lon, st["position"]["lat"], st["position"]["lon"])
                # Station is ahead if its order is greater than progress fraction
                st_frac = (st["order"] - 1) / max(1, len(self.stations) - 1)
                if st_frac * self.total_length_m >= curr_dist - 20:
                    next_st = st
                    dist_to_st = max(0.0, d)
                    break
        else:
            next_st = self.stations[0]
            dist_to_st = 300.0
            for st in reversed(self.stations):
                d = haversine_m(cur_lat, cur_lon, st["position"]["lat"], st["position"]["lon"])
                st_frac = (st["order"] - 1) / max(1, len(self.stations) - 1)
                if st_frac * self.total_length_m <= curr_dist + 20:
                    next_st = st
                    dist_to_st = max(0.0, d)
                    break

        eta_sec = round(dist_to_st / max(1.0, self.speed_mps), 1)

        return {
            "vehicle_id": "unit-demo-01",
            "route_id": "route-l2",
            "status": "online",
            "position": {"lat": round(cur_lat, 6), "lon": round(cur_lon, 6)},
            "speed_mps": round(self.speed_mps, 1),
            "accuracy_m": 3.8,
            "heading_deg": round(heading, 1),
            "occupancy_level": "medium",
            "last_update": datetime.now(timezone.utc).isoformat(),
            "navigation": {
                "direction": direction,
                "direction_source": "history",
                "direction_label": direction_label,
                "progress_m": round(curr_dist, 1),
                "route_length_m": round(self.total_length_m, 1),
                "route_progress": round(curr_dist / max(1.0, self.total_length_m), 3),
                "next_station": {"station_id": next_st["station_id"], "name": next_st["name"]},
                "distance_remaining_m": round(dist_to_st, 1),
                "eta_seconds": eta_sec,
                "eta_speed_mps": round(self.speed_mps, 1),
            },
        }


sim = RouteSimulation()


class MockApiHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Concise logging
        sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] {self.command} {self.path} -> {args[1]}\n")

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, Accept")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path in ("", "/v1/health"):
            self._reply_json({"status": "ok"})
        elif path == "/v1/ready":
            self._reply_json({"status": "ready", "database": "ok", "postgis_version": "3.4-sim"})
        elif path == "/v1/routes":
            self._reply_json({
                "routes": [{
                    "route_id": "route-l2",
                    "name": "Mexibús Línea 2 · Servicio ordinario",
                    "active": True,
                    "line_id": "mexibus-l2",
                    "line_label": "L2",
                    "network_name": "Mexibús",
                    "service_id": "l2-ordinary",
                    "service_name": "Servicio ordinario",
                    "origin_name": "La Quebrada",
                    "destination_name": "Las Américas",
                    "direction_forward_label": "La Quebrada → Las Américas",
                    "direction_reverse_label": "Las Américas → La Quebrada",
                    "default_speed_mps": 8.0,
                }]
            })
        elif path == "/v1/routes/route-l2":
            self._reply_json({
                "route_id": "route-l2",
                "service_id": "l2-ordinary",
                "network_name": "Mexibús",
                "line_label": "L2",
                "origin_name": "La Quebrada",
                "destination_name": "Las Américas",
                "path": sim.path_points,
            })
        elif path in ("/v1/routes/route-l2/stations", "/v1/stations"):
            self._reply_json({"route_id": "route-l2", "stations": sim.stations})
        elif path in ("/v1/vehicles", "/v1/vehicles/unit-demo-01"):
            vehicle = sim.get_vehicle_state()
            if path == "/v1/vehicles":
                self._reply_json({"vehicles": [vehicle]})
            else:
                self._reply_json(vehicle)
        elif path == "/v1/alerts":
            self._reply_json({
                "alerts": [{
                    "alert_id": "alert-01",
                    "route_id": "route-l2",
                    "vehicle_id": "unit-demo-01",
                    "type": "traffic",
                    "message": "Tráfico moderado en Vía José López Portillo",
                    "severity": "warning",
                    "active": True,
                }]
            })
        else:
            self.send_response(404)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"not_found"}')

    def _reply_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    server = ThreadingHTTPServer((HOST, PORT), MockApiHandler)
    print("=" * 66)
    print(f"🚀 Zentryx Mock API Server activo en: http://localhost:{PORT}")
    print(f"📡 Telemetría en vivo activa para: unit-demo-01 (Línea 2 Mexibús)")
    print(f"🌐 CORS habilitado para Flutter Web y Chrome")
    print(f"Para conectar la app móvil:")
    print(f"  flutter run -d chrome --dart-define=ZENTRYX_API_BASE_URL=http://localhost:{PORT}")
    print("=" * 66, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.", flush=True)


if __name__ == "__main__":
    main()
