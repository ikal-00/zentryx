"""Pure validation of API v1 payloads; no HTTP or database dependency."""

from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any

MAX_FUTURE_SKEW = timedelta(minutes=5)
MAX_EVENT_AGE = timedelta(hours=24)


class PayloadValidationError(ValueError):
    """Raised when a client payload does not satisfy the v1 contract."""

    def __init__(self, field: str, message: str):
        super().__init__(message)
        self.field = field
        self.message = message


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PayloadValidationError(field, "must_be_number")
    return float(value)


def _optional_number(
    value: Any,
    field: str,
    *,
    minimum: float | None = None,
    maximum_exclusive: float | None = None,
) -> float | None:
    if value is None:
        return None
    number = _number(value, field)
    if minimum is not None and number < minimum:
        raise PayloadValidationError(field, f"must_be_gte_{minimum:g}")
    if maximum_exclusive is not None and number >= maximum_exclusive:
        raise PayloadValidationError(field, f"must_be_lt_{maximum_exclusive:g}")
    return number


def _utc_datetime(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise PayloadValidationError(field, "must_be_iso8601_utc")
    raw = value.strip()
    candidate = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise PayloadValidationError(field, "must_be_iso8601_utc") from exc
    if parsed.tzinfo is None:
        raise PayloadValidationError(field, "timezone_required")
    return parsed.astimezone(timezone.utc)


def _bounded_timestamp(value: Any, field: str, now: datetime | None = None) -> str:
    parsed = _utc_datetime(value, field)
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if parsed > current + MAX_FUTURE_SKEW:
        raise PayloadValidationError(field, "too_far_in_future")
    if parsed < current - MAX_EVENT_AGE:
        raise PayloadValidationError(field, "too_old")
    return parsed.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _position(value: Any, *, telemetry: bool) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PayloadValidationError("position", "must_be_object")
    if "lat" not in value or "lon" not in value:
        raise PayloadValidationError("position", "lat_and_lon_required")

    lat = _number(value["lat"], "position.lat")
    lon = _number(value["lon"], "position.lon")
    if not -90 <= lat <= 90:
        raise PayloadValidationError("position.lat", "out_of_range")
    if not -180 <= lon <= 180:
        raise PayloadValidationError("position.lon", "out_of_range")

    normalized: dict[str, Any] = {"lat": lat, "lon": lon}
    if not telemetry:
        return normalized

    normalized["speed_mps"] = _optional_number(
        value.get("speed_mps"), "position.speed_mps", minimum=0
    )
    normalized["accuracy_m"] = _optional_number(
        value.get("accuracy_m"), "position.accuracy_m", minimum=0
    )
    normalized["heading_deg"] = _optional_number(
        value.get("heading_deg"),
        "position.heading_deg",
        minimum=0,
        maximum_exclusive=360,
    )

    satellites = value.get("satellites")
    if satellites is None:
        normalized["satellites"] = None
    elif isinstance(satellites, bool) or not isinstance(satellites, int) or satellites < 0:
        raise PayloadValidationError("position.satellites", "must_be_non_negative_integer")
    else:
        normalized["satellites"] = satellites
    return normalized


def validate_telemetry_payload(data: Any, *, now: datetime | None = None) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise PayloadValidationError("body", "must_be_object")

    required = ("schema_version", "device_id", "vehicle_id", "seq", "observed_at", "position")
    missing = [field for field in required if field not in data]
    if missing:
        raise PayloadValidationError(missing[0], "required")
    if data["schema_version"] != 1:
        raise PayloadValidationError("schema_version", "unsupported_schema_version")

    device_id = data["device_id"]
    vehicle_id = data["vehicle_id"]
    if not isinstance(device_id, str) or not device_id.strip():
        raise PayloadValidationError("device_id", "must_be_non_empty_string")
    if not isinstance(vehicle_id, str) or not vehicle_id.strip():
        raise PayloadValidationError("vehicle_id", "must_be_non_empty_string")

    seq = data["seq"]
    if isinstance(seq, bool) or not isinstance(seq, int) or seq < 0:
        raise PayloadValidationError("seq", "must_be_non_negative_integer")

    return {
        "schema_version": 1,
        "device_id": device_id.strip(),
        "vehicle_id": vehicle_id.strip(),
        "seq": seq,
        "observed_at": _bounded_timestamp(data["observed_at"], "observed_at", now),
        "position": _position(data["position"], telemetry=True),
    }


def validate_incident_payload(data: Any, *, now: datetime | None = None) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise PayloadValidationError("body", "must_be_object")

    required = ("vehicle_id", "type", "description", "position", "observed_at")
    missing = [field for field in required if field not in data]
    if missing:
        raise PayloadValidationError(missing[0], "required")

    vehicle_id = data["vehicle_id"]
    incident_type = data["type"]
    description = data["description"]
    if not isinstance(vehicle_id, str) or not vehicle_id.strip():
        raise PayloadValidationError("vehicle_id", "must_be_non_empty_string")
    if not isinstance(incident_type, str) or not incident_type.strip():
        raise PayloadValidationError("type", "must_be_non_empty_string")
    if not isinstance(description, str) or not description.strip():
        raise PayloadValidationError("description", "must_be_non_empty_string")

    return {
        "vehicle_id": vehicle_id.strip(),
        "type": incident_type.strip(),
        "description": description.strip(),
        "position": _position(data["position"], telemetry=False),
        "observed_at": _bounded_timestamp(data["observed_at"], "observed_at", now),
    }
