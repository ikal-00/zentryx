from flask import Blueprint

rutas = Blueprint(
    "rutas",
    __name__,
    url_prefix="/v1/rutas"
);

@rutas.get("/")
def rutasC():
    