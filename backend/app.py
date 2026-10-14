"""Canonical Flask application entrypoint for Zentryx."""

import os

from flask import Flask
from psycopg import OperationalError
from werkzeug.exceptions import HTTPException

from .routes import (
    alerts_blueprint,
    health_blueprint,
    telemetry_blueprint,
    transit_blueprint,
    vehicles_blueprint,
)


from .config import create_pool
from .services.errors import AuthenticationError, AssignmentNotFound


def create_app(pool=None) -> Flask:
    """Create the Zentryx API v1 application.

    A pool can be injected by tests. In normal execution it is created from
    POSTGRES_URL and exposed through ``app.extensions["POOL"]``.
    """
    app = Flask(__name__)

    if pool is None:
        pool = create_pool()

    app.extensions["POOL"] = pool

    app.register_blueprint(health_blueprint)
    app.register_blueprint(transit_blueprint)
    app.register_blueprint(vehicles_blueprint)
    app.register_blueprint(telemetry_blueprint)
    app.register_blueprint(alerts_blueprint)

    @app.after_request
    def enable_cors(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept"
        return response

    @app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
    @app.route("/<path:path>", methods=["OPTIONS"])
    def options_handler(path=""):
        return "", 204

    @app.errorhandler(AuthenticationError)
    def unauthorized(error):
        return {"error": str(error)}, 401

    @app.errorhandler(AssignmentNotFound)
    def assignment_missing(error):
        return {"error": str(error)}, 404

    @app.errorhandler(OperationalError)
    def database_unavailable(error):
        app.logger.exception("Database unavailable", exc_info=error)
        return {"error": "database_unavailable"}, 503

    @app.errorhandler(HTTPException)
    def http_error(error):
        return {"error": error.name.lower().replace(" ", "_")}, error.code

    @app.errorhandler(Exception)
    def unexpected_error(error):
        app.logger.exception("Unhandled API error", exc_info=error)
        return {"error": "internal_server_error"}, 500

    return app


def main() -> None:
    """Run the development server."""
    create_app().run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
    )


if __name__ == "__main__":
    main()
