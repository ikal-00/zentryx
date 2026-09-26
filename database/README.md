# Base de datos de Zentryx

PostgreSQL + PostGIS es la fuente de verdad del backend compartido.

## Estructura

```text
database/
├── schema.sql
├── migrations/
└── legacy/
```

`schema.sql` representa una instalación nueva. Las migraciones actualizan bases ya creadas.

## Base nueva

```bash
psql "$POSTGRES_URL" -f database/schema.sql
```

## Base existente

```bash
psql "$POSTGRES_URL" -f database/migrations/002_api_alignment.sql
psql "$POSTGRES_URL" -f database/migrations/003_runtime_hardening.sql
```

No reescribas migraciones que ya pudieron ejecutarse en el servidor compartido.

## Seed de Línea 2

```bash
POSTGRES_URL="$POSTGRES_URL" python -m backend.seed_routes
```

El seed usa `app/assets/routes/` y hace upsert de ruta, estaciones y orden.

## Legacy

`legacy/` conserva referencias históricas que no deben ejecutarse.

## Tokens

`devices.token_hash` y `drivers.token_hash` usan `sha256:<64 caracteres hexadecimales>`.
