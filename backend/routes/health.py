from flask import Blueprint, current_app


status = Blueprint("status", __name__, url_prefix="/v1")


@status.get("/health")
def status_response():
    """Liveness: Flask process is running."""
    return {"status": "ok"}, 200


@status.get("/ready")
def readiness_response():
    """Readiness: database and PostGIS are available."""
    pool = current_app.extensions["POOL"]
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1, PostGIS_Version();")
                row = cur.fetchone()
    except Exception:
        current_app.logger.exception("Readiness check failed")
        return {"status": "not_ready", "database": "unavailable"}, 503

    return {
        "status": "ready",
        "database": "ok",
        "postgis_version": row[1],
    }, 200
