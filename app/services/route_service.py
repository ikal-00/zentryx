"""Carga y valida definiciones de rutas sin acoplarlas a la interfaz Flet."""

from __future__ import annotations

import json
from ..models import RouteDefinition, StationDefinition
from pathlib import Path


ROUTES_DIR = Path(__file__).resolve().parents[1] / "assets" / "routes"

# Añadir aquí nuevas variantes (L2A, exprés, otras líneas) sin tocar el mapa.
SERVICE_ASSETS = {
    "l2-ordinary": {
        "route": "l2_ordinary_route.geojson",
        "stations": "l2_ordinary_stations.geojson",
    },
}


def available_services() -> tuple[str, ...]:
    return tuple(SERVICE_ASSETS)


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_route(service_id: str) -> RouteDefinition:
    try:
        assets = SERVICE_ASSETS[service_id]
    except KeyError as exc:
        raise ValueError(f"Servicio desconocido: {service_id}") from exc

    route_path = ROUTES_DIR / assets["route"]
    stations_path = ROUTES_DIR / assets["stations"]
    route_data = _load_json(route_path)
    stations_data = _load_json(stations_path)

    route_features = [
        feature
        for feature in route_data.get("features", [])
        if feature.get("geometry", {}).get("type") == "LineString"
    ]
    if len(route_features) != 1:
        raise ValueError(f"{route_path.name} debe contener exactamente un LineString de ruta")

    route_feature = route_features[0]
    props = route_feature.get("properties", {})
    coordinates = tuple(
        (float(lat), float(lon)) for lon, lat in route_feature["geometry"]["coordinates"]
    )
    if len(coordinates) < 2:
        raise ValueError(f"{route_path.name} no contiene una geometría válida")

    stations = []
    for feature in stations_data.get("features", []):
        if feature.get("geometry", {}).get("type") != "Point":
            continue

        station_props = feature.get("properties", {})
        if "stop_order" not in station_props:
            continue

        lon, lat = feature["geometry"]["coordinates"]
        stations.append(
            StationDefinition(
                station_id=str(station_props.get("station_id", feature.get("id", ""))),
                name=str(station_props.get("name", "Estación")),
                stop_order=int(station_props["stop_order"]),
                lat=float(lat),
                lon=float(lon),
            )
        )

    stations.sort(key=lambda station: station.stop_order)
    if not stations:
        raise ValueError(f"{stations_path.name} no contiene estaciones ordenadas")

    expected_orders = list(range(1, len(stations) + 1))
    actual_orders = [station.stop_order for station in stations]
    if actual_orders != expected_orders:
        raise ValueError(
            f"{stations_path.name} tiene stop_order incompleto o duplicado: {actual_orders}"
        )

    names = [station.name for station in stations]
    if len(names) != len(set(names)):
        raise ValueError(f"{stations_path.name} contiene nombres duplicados")

    expected_count = props.get("station_count")
    if expected_count is not None and int(expected_count) != len(stations):
        raise ValueError(
            f"{route_path.name} declara {expected_count} estaciones, "
            f"pero {stations_path.name} contiene {len(stations)}"
        )

    origin_name = str(props.get("origin_name", stations[0].name))
    destination_name = str(props.get("destination_name", stations[-1].name))
    if stations[0].name != origin_name or stations[-1].name != destination_name:
        raise ValueError(
            f"Las terminales declaradas ({origin_name} → {destination_name}) "
            "no coinciden con stop_order"
        )

    return RouteDefinition(
        route_id=str(props.get("route_id", "")),
        line_id=str(props.get("line_id", "")),
        line_label=str(props.get("line_label", "")),
        network_name=str(props.get("network_name", "")),
        service_id=str(props.get("service_id", service_id)),
        service_name=str(props.get("service_name", "")),
        origin_name=origin_name,
        destination_name=destination_name,
        forward_label=str(
            props.get(
                "direction_forward_label",
                f"{origin_name} → {destination_name}",
            )
        ),
        reverse_label=str(
            props.get(
                "direction_reverse_label",
                f"{destination_name} → {origin_name}",
            )
        ),
        coordinates=coordinates,
        stations=tuple(stations),
        route_source_path=route_path,
        stations_source_path=stations_path,
    )
