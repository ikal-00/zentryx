# Zentryx · Base de datos

La fuente de verdad actual es `database_v1.sql`.

## Base nueva

```bash
psql "$POSTGRES_URL" -f BD/database_v1.sql
```

Incluye PostGIS, rutas/servicios, estaciones, dispositivos, unidades, conductores, asignaciones, telemetría, alertas, incidentes y `vehicle_latest_telemetry`.

## Base existente

Ejecuta las migraciones en orden:

```bash
psql "$POSTGRES_URL" -f BD/migrations/002_api_alignment.sql
psql "$POSTGRES_URL" -f BD/migrations/003_runtime_hardening.sql
```

`003_runtime_hardening.sql` añade metadata de red/velocidad de ruta, elimina la restricción que impedía compartir nombre comercial entre servicios y crea autenticación/asignación de conductores.

## Cargar la Línea 2

Después del esquema/migraciones:

```bash
POSTGRES_URL="$POSTGRES_URL" python -m backend.seed_routes
```

El importador lee `app/assets/routes/l2_ordinary_route.geojson` y `l2_ordinary_stations.geojson`, hace upsert de la ruta, las 43 estaciones y su `stop_order`.

## Archivo legado

`Gps_sql/Gps_sql.sql` está deprecado y no debe ejecutarse.

## Tokens

`devices.token_hash` y `drivers.token_hash` almacenan:

```text
sha256:<64 caracteres hexadecimales>
```

Generación rápida:

```bash
python -c "import hashlib; t='TU_TOKEN'; print('sha256:'+hashlib.sha256(t.encode()).hexdigest())"
```
