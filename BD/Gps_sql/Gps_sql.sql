CREATE EXTENSION postgis;

CREATE TABLE estaciones (
    id SERIAL PRIMARY KEY,
    nombre TEXT,
    pocision geometry(Point , 4326)
)
