"""Vehicle HTTP endpoints. Navigation and persistence are separate modules."""

from flask import Blueprint, current_app
from ..services import vehicles

vehiculos = Blueprint("vehiculos", __name__, url_prefix="/v1")


@vehiculos.get("/vehicles")
def list_vehicles():
    return {"vehicles": vehicles.list_vehicles(current_app.extensions["POOL"])}, 200


@vehiculos.get("/vehicles/<string:vehicle_id>")
def get_vehicle(vehicle_id):
    vehicle = vehicles.get_vehicle(current_app.extensions["POOL"], vehicle_id)
    if vehicle is None:
        return {"error": "vehicle_not_found"}, 404
    return vehicle, 200
