import json

from flask import Blueprint, current_app, request
from ..repositories import transit as repository


rutas = Blueprint("rutas", __name__, url_prefix="/v1")


def _route_payload(row):
    return {
        "route_id": row[0],
        "name": row[1],
        "active": row[2],
        "line_id": row[3],
        "line_label": row[4],
        "network_name": row[5],
        "service_id": row[6],
        "service_name": row[7],
        "origin_name": row[8],
        "destination_name": row[9],
        "direction_forward_label": row[10],
        "direction_reverse_label": row[11],
        "default_speed_mps": row[12],
    }


@rutas.get("/routes")
def list_routes():
    pool = current_app.extensions["POOL"]
    active_only = request.args.get("active", "true").lower() not in {"0", "false", "no"}
    rows = repository.list_routes(pool, active_only)
    return {"routes": [_route_payload(row) for row in rows]}, 200


@rutas.get("/routes/<string:route_id>")
def route_detail(route_id):
    pool = current_app.extensions["POOL"]
    row = repository.route_detail(pool, route_id)

    if row is None:
        return {"error": "route_not_found"}, 404

    payload = _route_payload(row)
    geometry = json.loads(row[13]) if row[13] else None
    payload["path"] = (
        [{"lat": float(lat), "lon": float(lon)} for lon, lat in geometry.get("coordinates", [])]
        if geometry and geometry.get("type") == "LineString"
        else []
    )
    return payload, 200


@rutas.get("/routes/<string:route_id>/stations")
def route_stations(route_id):
    pool = current_app.extensions["POOL"]
    rows = repository.route_stations(pool, route_id)
    if rows is None:
        return {"error": "route_not_found"}, 404

    return {
        "route_id": route_id,
        "stations": [
            {
                "station_id": row[0],
                "name": row[1],
                "position": {"lat": row[2], "lon": row[3]},
                "active": row[4],
                "order": row[5],
            }
            for row in rows
        ],
    }, 200


@rutas.get("/stations")
def list_stations():
    pool = current_app.extensions["POOL"]
    rows = repository.list_stations(pool)

    return {
        "stations": [
            {
                "station_id": row[0],
                "name": row[1],
                "position": {"lat": row[2], "lon": row[3]},
                "active": row[4],
            }
            for row in rows
        ]
    }, 200
