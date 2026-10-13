-- Zentryx database schema v1
-- PostgreSQL + PostGIS
-- Coherente con contracts/api_v1.md
--
-- Fuente de verdad para rutas, estaciones, unidades, GPS,
-- telemetría, alertas, conductores e incidentes.

BEGIN;

CREATE EXTENSION IF NOT EXISTS postgis;

-- =========================================================
-- RUTAS / SERVICIOS
-- =========================================================

CREATE TABLE IF NOT EXISTS routes (
    route_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    line_id TEXT,
    line_label TEXT,
    network_name TEXT,
    service_id TEXT,
    service_name TEXT,
    origin_name TEXT,
    destination_name TEXT,
    direction_forward_label TEXT,
    direction_reverse_label TEXT,
    default_speed_mps DOUBLE PRECISION NOT NULL DEFAULT 6.0
        CHECK (default_speed_mps > 0),
    path geometry(LineString, 4326),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE routes
    ADD COLUMN IF NOT EXISTS line_id TEXT,
    ADD COLUMN IF NOT EXISTS line_label TEXT,
    ADD COLUMN IF NOT EXISTS network_name TEXT,
    ADD COLUMN IF NOT EXISTS service_id TEXT,
    ADD COLUMN IF NOT EXISTS service_name TEXT,
    ADD COLUMN IF NOT EXISTS origin_name TEXT,
    ADD COLUMN IF NOT EXISTS destination_name TEXT,
    ADD COLUMN IF NOT EXISTS direction_forward_label TEXT,
    ADD COLUMN IF NOT EXISTS direction_reverse_label TEXT,
    ADD COLUMN IF NOT EXISTS default_speed_mps DOUBLE PRECISION NOT NULL DEFAULT 6.0;

-- Variantes de una misma línea pueden compartir nombre comercial.
ALTER TABLE routes DROP CONSTRAINT IF EXISTS routes_name_key;

CREATE INDEX IF NOT EXISTS idx_routes_name
    ON routes(name);

CREATE INDEX IF NOT EXISTS idx_routes_path_gist
    ON routes USING GIST (path);

CREATE UNIQUE INDEX IF NOT EXISTS idx_routes_service_id_unique
    ON routes(service_id)
    WHERE service_id IS NOT NULL;

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

COMMENT ON COLUMN devices.token_hash IS
    'SHA-256 device token hash. Canonical format: sha256:<64 lowercase hex chars>.';

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
-- INCIDENTES DE OPERACIÓN
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

COMMIT;
