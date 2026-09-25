from flask import Blueprint


status = Blueprint("status", __name__, url_prefix="/v1")


@status.get("/health")
def status_response():
    return {"status": "ok"}, 200
