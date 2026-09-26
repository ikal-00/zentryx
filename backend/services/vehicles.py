"""Combine vehicle snapshots with navigation and API v1 presentation."""

import json
from ..navigation import RouteNavigator
from ..repositories import vehicles as repository


def _load_route_context(pool, route_id, cache):
    if not route_id:
        return None
    if route_id in cache:
        return cache[route_id]

    route_row, station_rows = repository.route_context(pool, route_id)
    if route_row is None:
        cache[route_id] = None
        return None

    geometry = json.loads(route_row[0])
    coordinates = [(float(lat), float(lon)) for lon, lat in geometry.get("coordinates", [])]
    stations = [
        {
            "station_id": row[0],
            "name": row[1],
            "stop_order": row[2],
            "lat": row[3],
            "lon": row[4],
        }
        for row in station_rows
    ]
    if len(coordinates) < 2 or not stations:
        cache[route_id] = None
        return None

    context = {
        "navigator": RouteNavigator(coordinates, stations),
        "forward_label": route_row[1],
        "reverse_label": route_row[2],
        "default_speed_mps": route_row[3] or 6.0,
    }
    cache[route_id] = context
    return context


def _serialize_vehicle(row, pool, route_cache):
    (
        vehicle_id,
        route_id,
        status,
        occupancy_level,
        lat,
        lon,
        speed_mps,
        accuracy_m,
        heading_deg,
        last_update,
        history,
        smoothed_speed_mps,
    ) = row

    navigation = None
    context = _load_route_context(pool, route_id, route_cache)
    if context is not None and lat is not None and lon is not None:
        history = history or []
        # First history item is normally the current packet. Exclude points that
        # project to the exact current sample from direction inference.
        older_history = history[1:] if len(history) > 1 else []
        result = context["navigator"].navigation(
            lat=lat,
            lon=lon,
            history=older_history,
            heading_deg=heading_deg,
            speed_mps=speed_mps,
            smoothed_speed_mps=smoothed_speed_mps,
            default_speed_mps=context["default_speed_mps"],
        )
        direction = (
            "forward"
            if result.direction == 1
            else "reverse"
            if result.direction == -1
            else "unknown"
        )
        direction_label = (
            context["forward_label"]
            if result.direction == 1
            else context["reverse_label"]
            if result.direction == -1
            else None
        )
        navigation = {
            "direction": direction,
            "direction_source": result.direction_source,
            "direction_label": direction_label,
            "progress_m": round(result.progress_m, 2) if result.progress_m is not None else None,
            "route_length_m": round(result.route_length_m, 2),
            "next_station": (
                {
                    "station_id": result.next_station_id,
                    "name": result.next_station_name,
                }
                if result.next_station_id is not None
                else None
            ),
            "distance_remaining_m": (
                round(result.distance_remaining_m, 2)
                if result.distance_remaining_m is not None
                else None
            ),
            "eta_seconds": (
                round(result.eta_seconds, 1) if result.eta_seconds is not None else None
            ),
            "eta_speed_mps": (
                round(result.eta_speed_mps, 2) if result.eta_speed_mps is not None else None
            ),
        }

    return {
        "vehicle_id": vehicle_id,
        "route_id": route_id,
        "status": status,
        "position": {"lat": lat, "lon": lon} if lat is not None and lon is not None else None,
        "speed_mps": speed_mps,
        "accuracy_m": accuracy_m,
        "heading_deg": heading_deg,
        "occupancy_level": occupancy_level,
        "last_update": last_update.isoformat().replace("+00:00", "Z") if last_update else None,
        "navigation": navigation,
    }


def list_vehicles(pool):
    cache = {}
    return [_serialize_vehicle(row, pool, cache) for row in repository.list_vehicles(pool)]


def get_vehicle(pool, vehicle_id):
    row = repository.get_vehicle(pool, vehicle_id)
    return None if row is None else _serialize_vehicle(row, pool, {})
