-- Zentryx purge driver schema migration
-- Drops driver tables and references in accordance with passenger-only focus.

BEGIN;

DROP TABLE IF EXISTS driver_vehicle_assignments CASCADE;
DROP TABLE IF EXISTS drivers CASCADE;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_incidents_driver'
    ) THEN
        ALTER TABLE incidents DROP CONSTRAINT fk_incidents_driver;
    END IF;
END $$;

ALTER TABLE incidents DROP COLUMN IF EXISTS driver_id;

COMMIT;
