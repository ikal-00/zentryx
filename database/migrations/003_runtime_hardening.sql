-- Zentryx runtime hardening migration
-- Run after 002_api_alignment.sql on existing databases.

BEGIN;

ALTER TABLE routes
    ADD COLUMN IF NOT EXISTS network_name TEXT,
    ADD COLUMN IF NOT EXISTS default_speed_mps DOUBLE PRECISION NOT NULL DEFAULT 6.0;

ALTER TABLE routes DROP CONSTRAINT IF EXISTS routes_name_key;

CREATE INDEX IF NOT EXISTS idx_routes_name
    ON routes(name);

CREATE TABLE IF NOT EXISTS drivers (
    driver_id TEXT PRIMARY KEY,
    display_name TEXT,
    token_hash TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON COLUMN drivers.token_hash IS
    'SHA-256 driver session/API token hash. Canonical format: sha256:<64 lowercase hex chars>.';

CREATE TABLE IF NOT EXISTS driver_vehicle_assignments (
    driver_id TEXT NOT NULL,
    vehicle_id TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (driver_id, vehicle_id),
    CONSTRAINT fk_driver_vehicle_driver
        FOREIGN KEY (driver_id) REFERENCES drivers(driver_id) ON DELETE CASCADE,
    CONSTRAINT fk_driver_vehicle_vehicle
        FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_driver_vehicle_active
    ON driver_vehicle_assignments(vehicle_id, active);

ALTER TABLE incidents
    ADD COLUMN IF NOT EXISTS driver_id TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_incidents_driver'
    ) THEN
        ALTER TABLE incidents
            ADD CONSTRAINT fk_incidents_driver
            FOREIGN KEY (driver_id)
            REFERENCES drivers(driver_id)
            ON DELETE SET NULL;
    END IF;
END $$;

COMMIT;
