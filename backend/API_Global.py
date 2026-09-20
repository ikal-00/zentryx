from flask import Flask
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool
import os
from .GPS import rutas
from .status import status
from .vehiculos import vehiculos

load_dotenv();
def create_app() -> Flask:
    app = Flask(__name__);

    app.register_blueprint(rutas);
    app.register_blueprint(status);
    app.register_blueprint(vehiculos);

    app.config["POOL"] = ConnectionPool (
        os.getenv("POSTGRES_URL"),
        min_size=5,
        max_size=30
    );
    return app;

if __name__ == "__main__":
    create_app().run();
