"""Shared validation and authentication helpers for Zentryx API v1."""

from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timezone
from typing import Any


class PayloadValidationError(ValueError):
    """Raised when a client payload does not satisfy the v1 contract."""

    def __init__(self, field: str, message: str):
        super().__init__(message)
        self.field = field
        self.message = message


def parse_device_authorization(header: str | None) -> str:
    if not header:
        raise PayloadValidationError("authorization", "missing_authorization")

    try:
        scheme, token = header.split(" ", 1)
    except ValueError as exc:
        raise PayloadValidationError("authorization", "invalid_authorization") from exc

    token = token.strip()
    if scheme != "Device" or not token:
        raise PayloadValidationError("authorization", "invalid_authorization")

    return token


def hash_device_token(token: str) -> str:
    """Canonical storage format for high-entropy device tokens."""
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def verify_device_token(stored_hash: str, token: str) -> bool:
    """Accept the canonical prefixed hash and legacy bare SHA-256 hashes."""
    expected = hash_device_token(token)
    candidate = str(stored_hash or "").strip()
    if candidate and not candidate.startswith("sha256:"):
        candidate = f"sha256:{candidate}"
    return hmac.compare_digest(candidate, expected)


def authenticate_vehicle_device(
    pool,
    *,
    vehicle_id: str,
    token: str,
    device_id: str | None = None,
) -> tuple[str | None, str | None]:
    """Return (device_id, error_code) for the device assigned to a vehicle."""
    if device_id is None:
        query = """
            SELECT d.device_id, d.token_hash, d.active, v.active
            FROM vehicles AS v
            JOIN devices AS d ON d.device_id = v.device_id
            WHERE v.vehicle_id = %s
        """
        params = (vehicle_id,)
    else:
        query = """
            SELECT d.device_id, d.token_hash, d.active, v.active
            FROM devices AS d
            JOIN vehicles AS v ON v.device_id = d.device_id
            WHERE d.device_id = %s AND v.vehicle_id = %s
        """
        params = (device_id, vehicle_id)

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            row = cur.fetchone()

    if row is None or not row[2] or not row[3]:
        return None, "device_or_vehicle_not_found"
    if not verify_device_token(row[1], token):
        return None, "invalid_authorization"
    return str(row[0]), None


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


def _utc_timestamp(value: Any, field: str) -> str:
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

    return (
        parsed.astimezone(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


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


def validate_telemetry_payload(data: Any) -> dict[str, Any]:
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
        "observed_at": _utc_timestamp(data["observed_at"], "observed_at"),
        "position": _position(data["position"], telemetry=True),
    }


def validate_incident_payload(data: Any) -> dict[str, Any]:
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
        "observed_at": _utc_timestamp(data["observed_at"], "observed_at"),
    }
