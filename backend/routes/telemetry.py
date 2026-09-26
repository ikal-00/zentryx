"""Device telemetry HTTP boundary."""

from flask import Blueprint, current_app
from ..auth import parse_device_authorization
from ..validation import PayloadValidationError, validate_telemetry_payload
from ..services.telemetry import accept_telemetry
from .helpers import _json_body, _authorization, _validation_error

telemetria = Blueprint("telemetria", __name__, url_prefix="/v1")


@telemetria.post("/telemetry")
def post_telemetry():
    data, error = _json_body()
    if error:
        return error

    token, error = _authorization(parse_device_authorization)
    if error:
        return error

    try:
        payload = validate_telemetry_payload(data)
    except PayloadValidationError as exc:
        return _validation_error(exc)

    return accept_telemetry(current_app.extensions["POOL"], payload, token), 202
