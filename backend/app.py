"""Canonical Flask application entrypoint for Zentryx."""

import os

from dotenv import load_dotenv
from flask import Flask
from psycopg import OperationalError
from psycopg_pool import ConnectionPool
from werkzeug.exceptions import HTTPException

from .routes import (
    health_blueprint,
    telemetry_blueprint,
    transit_blueprint,
    vehicles_blueprint,
)


load_dotenv()


def create_app(pool=None) -> Flask:
    """Create the Zentryx API v1 application.

    A pool can be injected by tests. In normal execution it is created from
    POSTGRES_URL and exposed through ``app.extensions["POOL"]``.
    """
    app = Flask(__name__)

    if pool is None:
        postgres_url = os.getenv("POSTGRES_URL")
        if not postgres_url:
            raise RuntimeError("POSTGRES_URL is required to start the Zentryx API")
        pool = ConnectionPool(
            conninfo=postgres_url,
            min_size=int(os.getenv("DB_POOL_MIN", "1")),
            max_size=int(os.getenv("DB_POOL_MAX", "30")),
            open=True,
        )

    app.extensions["POOL"] = pool

    app.register_blueprint(health_blueprint)
    app.register_blueprint(transit_blueprint)
    app.register_blueprint(vehicles_blueprint)
    app.register_blueprint(telemetry_blueprint)

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
