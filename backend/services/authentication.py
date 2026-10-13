"""Authenticate active devices."""

from __future__ import annotations
from ..auth import verify_token
from ..repositories import identities


def authenticate_vehicle_device(
    pool,
    *,
    vehicle_id: str,
    token: str,
    device_id: str | None = None,
) -> tuple[str | None, str | None]:
    """Return (device_id, error_code) for the active device assigned to a vehicle."""
    row = identities.device_assignment(pool, vehicle_id, device_id)

    if row is None or not row[2] or not row[3]:
        return None, "device_or_vehicle_not_found"
    if not verify_token(row[1], token):
        return None, "invalid_authorization"
    return str(row[0]), None
