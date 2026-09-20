from flask import Blueprint

status = Blueprint(
    "status",
    __name__,
    url_prefix="/"
);

@status.get("/health")
def status_Resp():
    return {"status": "ok"};