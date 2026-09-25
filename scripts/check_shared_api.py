#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def get_json(url: str):
    request = Request(url, headers={"Accept": "application/json"})
    with urlopen(request, timeout=5) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def check(condition: bool, label: str, detail: str = "") -> None:
    if not condition:
        suffix = f": {detail}" if detail else ""
        raise RuntimeError(f"FAIL {label}{suffix}")
    print(f"OK   {label}{f' · {detail}' if detail else ''}")


def main() -> int:
    base_url = (sys.argv[1] if len(sys.argv) > 1 else "http://100.72.215.34:5000").rstrip("/")
    vehicle_id = sys.argv[2] if len(sys.argv) > 2 else "unit-demo-01"

    try:
        status, ready = get_json(f"{base_url}/v1/ready")
        check(status == 200 and ready.get("status") == "ready", "API + PostgreSQL/PostGIS", str(ready))

        status, routes_payload = get_json(f"{base_url}/v1/routes")
        routes = routes_payload.get("routes", [])
        route = next((item for item in routes if item.get("service_id") == "l2-ordinary"), None)
        check(status == 200 and route is not None, "Ruta L2 ordinaria", route.get("route_id") if route else "no encontrada")
        route_id = route["route_id"]

        status, detail = get_json(f"{base_url}/v1/routes/{route_id}")
        path = detail.get("path", [])
        check(status == 200 and len(path) > 50, "Geometría de ruta", f"{len(path)} puntos")

        status, stations_payload = get_json(f"{base_url}/v1/routes/{route_id}/stations")
        stations = stations_payload.get("stations", [])
        check(status == 200 and len(stations) == 43, "Estaciones", f"{len(stations)} cargadas")

        status, vehicle = get_json(f"{base_url}/v1/vehicles/{vehicle_id}")
        navigation = vehicle.get("navigation") or {}
        next_station = navigation.get("next_station") or {}
        check(status == 200 and vehicle.get("status") == "online", "Unidad demo online", vehicle_id)
        check(vehicle.get("position") is not None, "Posición GPS", str(vehicle.get("position")))
        check(navigation.get("direction") in {"forward", "reverse"}, "Dirección", str(navigation.get("direction")))
        check(navigation.get("eta_seconds") is not None, "ETA backend", f"{navigation.get('eta_seconds')} s")
        check(bool(next_station.get("name")), "Próxima estación", str(next_station.get("name")))

        query = urlencode({"route_id": route_id, "vehicle_id": vehicle_id})
        status, alerts_payload = get_json(f"{base_url}/v1/alerts?{query}")
        alerts = alerts_payload.get("alerts", [])
        check(status == 200 and len(alerts) >= 1, "Alertas activas", f"{len(alerts)}")

    except (HTTPError, URLError, TimeoutError, RuntimeError, KeyError, json.JSONDecodeError) as error:
        print(f"\nShared API check failed: {error}", file=sys.stderr)
        print("Si falla unidad/ETA/alertas, inicia el perfil demo en el servidor:", file=sys.stderr)
        print("  docker compose --profile demo up -d --build", file=sys.stderr)
        return 1

    print("\nZentryx shared API: end-to-end OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
