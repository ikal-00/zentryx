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
    Conten_type = request.headers.get("pocision/json");
    autorization = request.headers.get("Authorization");
    data = request.get_json();
    pool = current_app.extensions["POOL"];

    scheme,auth = autorization.split(" ",1);

    with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                     """
                                   
                
                """);

    return {
        "accepted": True,
        "device_id": data["device_id"],
        "seq": data["seq"]
    }, 202;