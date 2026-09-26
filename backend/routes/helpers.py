"""Shared HTTP request parsing and validation responses."""

from flask import request
from ..validation import PayloadValidationError


def _json_body():
    if not request.is_json:
        return None, ({"error": "invalid_content_type"}, 400)
    data = request.get_json(silent=True)
    if data is None:
        return None, ({"error": "invalid_json"}, 400)
    return data, None


def _authorization(parser):
    try:
        return parser(request.headers.get("Authorization")), None
    except PayloadValidationError as exc:
        return None, ({"error": exc.message}, 401)


def _validation_error(exc):
    return {
        "error": "invalid_data",
        "field": exc.field,
        "detail": exc.message,
    }, 422
