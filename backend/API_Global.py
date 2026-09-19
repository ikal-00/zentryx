from flask import Flask
from dotenv import load_dotenv
import os
from .GPS import rutas

load_dotenv()
def create_app() -> Flask:
    app = Flask(__name__);

    app.register_blueprint(rutas);


    return app;


if __name__ == "__main__":
    create_app().run();
