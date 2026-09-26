"""Read-only alert HTTP endpoint."""

from flask import Blueprint, current_app, request
from ..repositories import alerts as repository

alertas = Blueprint("alertas", __name__, url_prefix="/v1")


@alertas.get("/alerts")
def list_alerts():
    rows = repository.list_alerts(
        current_app.extensions["POOL"], request.args.get("route_id"), request.args.get("vehicle_id")
    )
    return {
        "alerts": [
            {
                "alert_id": row[0],
                "route_id": row[1],
                "vehicle_id": row[2],
                "type": row[3],
                "message": row[4],
                "severity": row[5],
                "created_at": row[6].isoformat().replace("+00:00", "Z"),
                "active": row[7],
            }
            for row in rows
        ]
    }, 200
