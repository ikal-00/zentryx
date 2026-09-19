from flask import Blueprint

rutas = Blueprint(
    "rutas",
    __name__,
    url_prefix="/rutas"
);

@rutas.get("/")
def rutasC():
    