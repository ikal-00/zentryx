from flask import Blueprint
from flask import current_app
from flask import request


telemetria = Blueprint(
    "telemetria",
    __name__,
    url_prefix="/"
)

@telemetria.post("/v1/telemetry")
def Telemetry():
    data = request.get_json();

    

