"""Compatibility exports; new code imports auth, validation or services directly."""

from .auth import (
    hash_device_token,
    hash_token,
    parse_device_authorization,
    verify_device_token,
    verify_token,
)
from .services.authentication import authenticate_vehicle_device
from .validation import (
    MAX_EVENT_AGE,
    MAX_FUTURE_SKEW,
    PayloadValidationError,
    validate_telemetry_payload,
)

__all__ = [
    "hash_device_token",
    "hash_token",
    "parse_device_authorization",
    "verify_device_token",
    "verify_token",
    "authenticate_vehicle_device",
    "MAX_EVENT_AGE",
    "MAX_FUTURE_SKEW",
    "PayloadValidationError",
    "validate_telemetry_payload",
]
