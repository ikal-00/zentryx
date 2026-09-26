"""Compose local or API-backed passenger data sources."""

import logging
from dataclasses import dataclass
from ..config import ACTIVE_SERVICE_ID, AppSettings
from ..models import RouteDefinition
from . import ApiAlertService, ApiVehicleService, VehicleService, load_route, load_route_from_api


@dataclass(frozen=True)
class PassengerSources:
    route: RouteDefinition
    vehicle: VehicleService
    alerts: ApiAlertService | None
    route_from_api: bool
    demo: bool


def create_sources(settings: AppSettings) -> PassengerSources:
    api_base_url = settings.api_base_url
    service_id = settings.service_id
    route_from_api = False
    route = None
    if api_base_url:
        try:
            route = load_route_from_api(
                api_base_url,
                service_id=service_id,
            )
            route_from_api = True
        except Exception:
            logging.getLogger(__name__).exception(
                "Could not load route from API; using local route asset"
            )

    if route is None:
        route = load_route(service_id if service_id in (ACTIVE_SERVICE_ID,) else ACTIVE_SERVICE_ID)

    route_coordinates = list(route.coordinates)

    if api_base_url:
        vehicle_id = settings.vehicle_id
        vehicle_service = ApiVehicleService(
            route_coordinates=route_coordinates,
            base_url=api_base_url,
            vehicle_id=vehicle_id,
            route_id=route.route_id,
            forward_direction_label=route.forward_label,
            reverse_direction_label=route.reverse_label,
        )
        alert_service = ApiAlertService(
            base_url=api_base_url,
            route_id=route.route_id,
            vehicle_id=vehicle_id,
        )
        demo_source = False
    else:
        vehicle_service = VehicleService(
            route_coordinates=route_coordinates,
            route_id=route.route_id,
            forward_direction_label=route.forward_label,
            reverse_direction_label=route.reverse_label,
        )
        alert_service = None
        demo_source = True

    return PassengerSources(route, vehicle_service, alert_service, route_from_api, demo_source)
