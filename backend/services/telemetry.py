"""Authorize telemetry and preserve duplicate acknowledgement semantics."""

from .authentication import authenticate_vehicle_device
from .errors import AuthenticationError, AssignmentNotFound
from ..repositories import telemetry as repository


def accept_telemetry(pool, payload, token):
    _, auth_error = authenticate_vehicle_device(
        pool,
        vehicle_id=payload["vehicle_id"],
        device_id=payload["device_id"],
        token=token,
    )
    if auth_error == "invalid_authorization":
        raise AuthenticationError(auth_error)
    if auth_error:
        raise AssignmentNotFound(auth_error)
    inserted = repository.insert_telemetry(pool, payload)

    response = {
        "accepted": True,
        "device_id": payload["device_id"],
        "seq": payload["seq"],
    }
    if not inserted:
        response["duplicate"] = True
    return response
