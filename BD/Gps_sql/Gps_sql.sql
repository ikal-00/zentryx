CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE estaciones (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    pocision geometry(Point , 4326) NOT NULL
);

CREATE TABLE rutas (
    id SERIAL PRIMARY KEY,
    nombre_ruta TEXT NOT NULL UNIQUE,
);

CREATE TABLE comp_ruta (
    id SERIAL PRIMARY KEY,
    ruta_id INTEGER NOT NULL,
    estacion_id INTEGER NOT NULL,

    orden INTEGER NOT NULL,

    FOREIGN KEY (ruta_id)
        REFERENCES rutas(id),
    FOREIGN KEY (estacion_id)
        REFERENCES estaciones(id)
    
    UNIQUE (estacion_id,orden);
);
