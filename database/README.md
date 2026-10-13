# Base de datos de Zentryx

PostgreSQL + PostGIS es la fuente de verdad del backend compartido.

## Estructura

```text
database/
├── schema.sql
├── migrations/
└── legacy/
```

`schema.sql` representa una instalación nueva. Las migraciones actualizan bases ya creadas. Esta reorganización conserva los archivos SQL sin cambios y no necesita migrar datos.

Compose inicializa el esquema solo cuando el volumen está vacío. Reconstruir la API no reaplica migraciones. Conserva el proyecto `zentryx` y el volumen lógico `zentryx_db` (nombre Docker predeterminado `zentryx_zentryx_db`). Nunca elimines ese volumen.

Antes de aplicar migraciones a una base existente, verifica su estado y prepara un respaldo. Los comandos de abajo son procedimientos operativos; no forman parte del despliegue automático.

## Base nueva

```bash
psql "$POSTGRES_URL" -f database/schema.sql
```

## Base existente

```bash
psql "$POSTGRES_URL" -f database/migrations/002_api_alignment.sql
psql "$POSTGRES_URL" -f database/migrations/003_runtime_hardening.sql
psql "$POSTGRES_URL" -f database/migrations/004_purge_driver_schema.sql
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

`devices.token_hash` usa `sha256:<64 caracteres hexadecimales>`.

## Pruebas

Solo `TEST_DATABASE_URL`, con nombre terminado en `_test`, habilita integración. La suite vacía tablas de esa base desechable. `POSTGRES_URL` queda reservado al runtime y nunca activa tests destructivos.
