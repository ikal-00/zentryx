"""Driver authorization and incident identity creation."""

from uuid import uuid4
from .authentication import authenticate_driver_vehicle
from .errors import AuthenticationError, AssignmentNotFound
from ..repositories import incidents as repository


def report_incident(pool, payload, token):
    driver_id, auth_error = authenticate_driver_vehicle(
        pool,
        vehicle_id=payload["vehicle_id"],
        token=token,
    )
    if auth_error == "invalid_authorization":
        raise AuthenticationError(auth_error)
    if auth_error:
        raise AssignmentNotFound(auth_error)

    incident_id = f"incident-{uuid4().hex[:12]}"
    repository.insert_incident(pool, payload, driver_id, incident_id)

    return {
        "incident_id": incident_id,
        "driver_id": driver_id,
        "created": True,
    }
