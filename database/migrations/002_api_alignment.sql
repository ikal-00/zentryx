-- Zentryx API v1 alignment migration
-- Run after database/schema.sql on existing databases.

BEGIN;

ALTER TABLE routes
    ADD COLUMN IF NOT EXISTS line_id TEXT,
    ADD COLUMN IF NOT EXISTS line_label TEXT,
    ADD COLUMN IF NOT EXISTS service_id TEXT,
    ADD COLUMN IF NOT EXISTS service_name TEXT,
    ADD COLUMN IF NOT EXISTS origin_name TEXT,
    ADD COLUMN IF NOT EXISTS destination_name TEXT,
    ADD COLUMN IF NOT EXISTS direction_forward_label TEXT,
    ADD COLUMN IF NOT EXISTS direction_reverse_label TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_routes_service_id_unique
    ON routes(service_id)
    WHERE service_id IS NOT NULL;

COMMENT ON COLUMN devices.token_hash IS
    'SHA-256 device token hash. Canonical format: sha256:<64 lowercase hex chars>.';

COMMIT;
