"""Load active route/service metadata, geometry and stations from the API."""

from __future__ import annotations

import json
from urllib.request import Request, urlopen

from ..models import RouteDefinition, StationDefinition


def _get_json(url: str, timeout: float = 4.0):
    request = Request(url, headers={"Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def load_route_from_api(
    base_url: str,
    *,
    service_id: str,
    timeout: float = 4.0,
) -> RouteDefinition:
    base_url = base_url.rstrip("/")
    routes_payload = _get_json(f"{base_url}/v1/routes", timeout)
    routes = routes_payload.get("routes") or []
    route_meta = next(
        (route for route in routes if route.get("service_id") == service_id),
        None,
    )
    if route_meta is None:
        raise ValueError(f"Service not found in API: {service_id}")

    route_id = str(route_meta["route_id"])
    detail = _get_json(f"{base_url}/v1/routes/{route_id}", timeout)
    stations_payload = _get_json(f"{base_url}/v1/routes/{route_id}/stations", timeout)

    coordinates = tuple(
        (float(point["lat"]), float(point["lon"])) for point in detail.get("path") or []
    )
    if len(coordinates) < 2:
        raise ValueError("API route has no usable path geometry")

    stations = []
    for item in stations_payload.get("stations") or []:
        position = item.get("position") or {}
        stations.append(
            StationDefinition(
                station_id=str(item["station_id"]),
                name=str(item["name"]),
                stop_order=int(item["order"]),
                lat=float(position["lat"]),
                lon=float(position["lon"]),
            )
        )
    stations.sort(key=lambda station: station.stop_order)
    if not stations:
        raise ValueError("API route has no active stations")

    expected = list(range(1, len(stations) + 1))
    if [station.stop_order for station in stations] != expected:
        raise ValueError("API route station order is incomplete or duplicated")

    return RouteDefinition(
        route_id=route_id,
        line_id=str(detail.get("line_id") or ""),
        line_label=str(detail.get("line_label") or ""),
        network_name=str(detail.get("network_name") or ""),
        service_id=str(detail.get("service_id") or service_id),
        service_name=str(detail.get("service_name") or ""),
        origin_name=str(detail.get("origin_name") or stations[0].name),
        destination_name=str(detail.get("destination_name") or stations[-1].name),
        forward_label=str(
            detail.get("direction_forward_label") or f"{stations[0].name} → {stations[-1].name}"
        ),
        reverse_label=str(
            detail.get("direction_reverse_label") or f"{stations[-1].name} → {stations[0].name}"
        ),
        coordinates=coordinates,
        stations=tuple(stations),
        route_source_path=None,
        stations_source_path=None,
    )
