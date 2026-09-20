-- Zentryx database schema v1
-- PostgreSQL + PostGIS
-- Coherente con contracts/api_v1.md
--
-- Este archivo NO reemplaza ni borra BD/Gps_sql/Gps_sql.sql.
-- Es la propuesta integrada v1 para rutas, estaciones, unidades, GPS,
-- telemetría, alertas e incidentes.

BEGIN;

CREATE EXTENSION IF NOT EXISTS postgis;

-- =========================================================
-- RUTAS
-- =========================================================

CREATE TABLE IF NOT EXISTS routes (
    route_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    path geometry(LineString, 4326),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_routes_path_gist
    ON routes USING GIST (path);

-- =========================================================
-- ESTACIONES
-- =========================================================

CREATE TABLE IF NOT EXISTS stations (
    station_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    position geometry(Point, 4326) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stations_position_gist
    ON stations USING GIST (position);

-- Una estación puede pertenecer a una o varias rutas.
CREATE TABLE IF NOT EXISTS route_stations (
    route_id TEXT NOT NULL,
    station_id TEXT NOT NULL,
    stop_order INTEGER NOT NULL CHECK (stop_order > 0),

    PRIMARY KEY (route_id, station_id),
    UNIQUE (route_id, stop_order),

    CONSTRAINT fk_route_stations_route
        FOREIGN KEY (route_id)
        REFERENCES routes(route_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_route_stations_station
        FOREIGN KEY (station_id)
        REFERENCES stations(station_id)
        ON DELETE CASCADE
);

-- =========================================================
-- DISPOSITIVOS GPS
-- =========================================================

CREATE TABLE IF NOT EXISTS devices (
    device_id TEXT PRIMARY KEY,
    name TEXT,
    token_hash TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =========================================================
-- UNIDADES
-- =========================================================

CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id TEXT PRIMARY KEY,
    display_name TEXT,
    route_id TEXT,
    device_id TEXT UNIQUE,

    status TEXT NOT NULL DEFAULT 'unknown'
        CHECK (status IN ('online', 'offline', 'unknown')),

    occupancy_level TEXT NOT NULL DEFAULT 'unknown'
        CHECK (occupancy_level IN ('low', 'medium', 'high', 'unknown')),

    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_vehicles_route
        FOREIGN KEY (route_id)
        REFERENCES routes(route_id)
        ON DELETE SET NULL,

    CONSTRAINT fk_vehicles_device
        FOREIGN KEY (device_id)
        REFERENCES devices(device_id)
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_vehicles_route_id
    ON vehicles(route_id);

-- =========================================================
-- TELEMETRÍA GPS
-- =========================================================

CREATE TABLE IF NOT EXISTS telemetry (
    id BIGSERIAL PRIMARY KEY,

    device_id TEXT NOT NULL,
    vehicle_id TEXT NOT NULL,
    sequence BIGINT NOT NULL CHECK (sequence >= 0),

    position geometry(Point, 4326) NOT NULL,

    speed_mps DOUBLE PRECISION
        CHECK (speed_mps IS NULL OR speed_mps >= 0),

    accuracy_m DOUBLE PRECISION
        CHECK (accuracy_m IS NULL OR accuracy_m >= 0),

    heading_deg DOUBLE PRECISION
        CHECK (
            heading_deg IS NULL
            OR (heading_deg >= 0 AND heading_deg < 360)
        ),

    satellites INTEGER
        CHECK (satellites IS NULL OR satellites >= 0),

    observed_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (device_id, sequence),

    CONSTRAINT fk_telemetry_device
        FOREIGN KEY (device_id)
        REFERENCES devices(device_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_telemetry_vehicle
        FOREIGN KEY (vehicle_id)
        REFERENCES vehicles(vehicle_id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_telemetry_position_gist
    ON telemetry USING GIST (position);

CREATE INDEX IF NOT EXISTS idx_telemetry_vehicle_observed_at
    ON telemetry(vehicle_id, observed_at DESC);

CREATE INDEX IF NOT EXISTS idx_telemetry_device_observed_at
    ON telemetry(device_id, observed_at DESC);

-- =========================================================
-- ALERTAS
-- =========================================================

CREATE TABLE IF NOT EXISTS alerts (
    alert_id TEXT PRIMARY KEY,
    route_id TEXT,
    vehicle_id TEXT,

    type TEXT NOT NULL,
    message TEXT NOT NULL,

    severity TEXT NOT NULL DEFAULT 'info'
        CHECK (severity IN ('info', 'warning', 'critical')),

    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,

    CONSTRAINT fk_alerts_route
        FOREIGN KEY (route_id)
        REFERENCES routes(route_id)
        ON DELETE SET NULL,

    CONSTRAINT fk_alerts_vehicle
        FOREIGN KEY (vehicle_id)
        REFERENCES vehicles(vehicle_id)
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_alerts_active_created_at
    ON alerts(active, created_at DESC);

-- =========================================================
-- INCIDENTES REPORTADOS POR CONDUCTOR
-- =========================================================

CREATE TABLE IF NOT EXISTS incidents (
    incident_id TEXT PRIMARY KEY,
    vehicle_id TEXT NOT NULL,

    type TEXT NOT NULL,
    description TEXT,
    position geometry(Point, 4326),

    observed_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,

    CONSTRAINT fk_incidents_vehicle
        FOREIGN KEY (vehicle_id)
        REFERENCES vehicles(vehicle_id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_incidents_position_gist
    ON incidents USING GIST (position);

CREATE INDEX IF NOT EXISTS idx_incidents_vehicle_created_at
    ON incidents(vehicle_id, created_at DESC);

-- =========================================================
-- VISTA: ÚLTIMA POSICIÓN CONOCIDA DE CADA UNIDAD
-- =========================================================
-- Esta vista simplifica GET /v1/vehicles y GET /v1/vehicles/{id}.

CREATE OR REPLACE VIEW vehicle_latest_telemetry AS
SELECT DISTINCT ON (t.vehicle_id)
    t.vehicle_id,
    t.device_id,
    ST_Y(t.position) AS lat,
    ST_X(t.position) AS lon,
    t.speed_mps,
    t.accuracy_m,
    t.heading_deg,
    t.satellites,
    t.observed_at AS last_update,
    t.received_at
FROM telemetry t
ORDER BY t.vehicle_id, t.observed_at DESC, t.id DESC;

-- =========================================================
-- EJEMPLOS DE INSERCIÓN PARA DESARROLLO
-- =========================================================
-- No se ejecutan automáticamente. Son solo referencia.
--
-- INSERT INTO routes (route_id, name)
-- VALUES ('route-l2', 'Mexibús Línea 2');
--
-- INSERT INTO stations (station_id, name, position)
-- VALUES (
--     'station-bandera-tultitlan',
--     'Bandera Tultitlán',
--     ST_SetSRID(ST_MakePoint(-99.16299, 19.62211), 4326)
-- );
--
-- INSERT INTO route_stations (route_id, station_id, stop_order)
-- VALUES ('route-l2', 'station-bandera-tultitlan', 1);
--
-- INSERT INTO devices (device_id, name, token_hash)
-- VALUES ('gps-01', 'GPS prototipo 01', '<HASH_DEL_TOKEN>');
--
-- INSERT INTO vehicles (vehicle_id, display_name, route_id, device_id)
-- VALUES ('unit-01', 'Unidad Demo 01', 'route-l2', 'gps-01');
--
-- INSERT INTO telemetry (
--     device_id,
--     vehicle_id,
--     sequence,
--     position,
--     speed_mps,
--     accuracy_m,
--     heading_deg,
--     satellites,
--     observed_at
-- ) VALUES (
--     'gps-01',
--     'unit-01',
--     152,
--     ST_SetSRID(ST_MakePoint(-99.16299, 19.62211), 4326),
--     8.3,
--     4.7,
--     124.5,
--     12,
--     '2026-09-20T05:31:22Z'
-- );

COMMIT;
