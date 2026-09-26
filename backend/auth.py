"""Authorization schemes and constant-time token verification."""

from __future__ import annotations
import hashlib
import hmac
from .validation import PayloadValidationError


def _parse_authorization(header: str | None, expected_scheme: str) -> str:
    if not header:
        raise PayloadValidationError("authorization", "missing_authorization")
    try:
        scheme, token = header.split(" ", 1)
    except ValueError as exc:
        raise PayloadValidationError("authorization", "invalid_authorization") from exc
    token = token.strip()
    if scheme != expected_scheme or not token:
        raise PayloadValidationError("authorization", "invalid_authorization")
    return token


def parse_device_authorization(header: str | None) -> str:
    return _parse_authorization(header, "Device")


def parse_driver_authorization(header: str | None) -> str:
    return _parse_authorization(header, "Driver")


def hash_token(token: str) -> str:
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def hash_device_token(token: str) -> str:
    return hash_token(token)


def verify_token(stored_hash: str, token: str) -> bool:
    expected = hash_token(token)
    candidate = str(stored_hash or "").strip()
    if candidate and not candidate.startswith("sha256:"):
        candidate = f"sha256:{candidate}"
    return hmac.compare_digest(candidate, expected)


def verify_device_token(stored_hash: str, token: str) -> bool:
    return verify_token(stored_hash, token)
