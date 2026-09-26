"""HTTP route blueprints for the Zentryx API."""

from .health import status as health_blueprint
from .telemetry import telemetria as telemetry_blueprint
from .transit import rutas as transit_blueprint
from .vehicles import vehiculos as vehicles_blueprint

__all__ = [
    "alerts_blueprint",
    "incidents_blueprint",
    "health_blueprint",
    "telemetry_blueprint",
    "transit_blueprint",
    "vehicles_blueprint",
]

from .alerts import alertas as alerts_blueprint
from .incidents import incidentes as incidents_blueprint
