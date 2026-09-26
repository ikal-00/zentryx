"""HTTP route blueprints for the Zentryx API."""

from .health import status as health_blueprint
from .telemetry import telemetria as telemetry_blueprint
from .transit import rutas as transit_blueprint
from .vehicles import vehiculos as vehicles_blueprint

__all__ = [
    "health_blueprint",
    "telemetry_blueprint",
    "transit_blueprint",
    "vehicles_blueprint",
]
