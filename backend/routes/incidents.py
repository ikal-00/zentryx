"""Driver incident HTTP boundary."""

from flask import Blueprint, current_app
from ..auth import parse_driver_authorization
from ..validation import PayloadValidationError, validate_incident_payload
from ..services.incidents import report_incident
from .helpers import _json_body, _authorization, _validation_error

incidentes = Blueprint("incidentes", __name__, url_prefix="/v1")


@incidentes.post("/incidents")
def create_incident():
    data, error = _json_body()
    if error:
        return error

    token, error = _authorization(parse_driver_authorization)
    if error:
        return error

    try:
        payload = validate_incident_payload(data)
    except PayloadValidationError as exc:
        return _validation_error(exc)

    return report_incident(current_app.extensions["POOL"], payload, token), 201
