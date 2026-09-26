# Zentryx backend · API v1

`backend/app.py` es el entrypoint canónico de Flask. `API_Global.py` se conserva como compatibilidad temporal.

## Setup

Desde la raíz:

```bash
make setup
source .venv/bin/activate
```

Variables principales:

```text
POSTGRES_URL=postgresql://user:password@localhost:5432/zentryx
DB_POOL_MIN=1
DB_POOL_MAX=10
HOST=0.0.0.0
PORT=5000
```

## Organización

```text
backend/
├── app.py             App factory y entrypoint
├── routes/            Blueprints HTTP
├── api_utils.py       Validación y autenticación
├── navigation.py      Proyección, dirección y ETA
├── seed_routes.py     Seed de Línea 2
├── dev_simulator.py   Telemetría demo compartida
└── tests/             Unit + integración PostGIS
```

## Base de datos

```bash
psql "$POSTGRES_URL" -f database/schema.sql
POSTGRES_URL="$POSTGRES_URL" python -m backend.seed_routes
```

Migraciones para una base existente están en `database/migrations/`.

## Ejecutar sin Docker

```bash
python -m backend.app
```

## Servidor compartido

```bash
docker compose --profile demo up -d --build
```

El perfil `demo` crea `unit-demo-01` y publica telemetría por la API real. No requiere GPS físico.

```bash
python3 scripts/check_shared_api.py http://<TAILSCALE_IP>:5000
```

No uses `docker compose down -v` salvo que quieras borrar deliberadamente la base de desarrollo.

## Endpoints MVP

```text
GET  /v1/health
GET  /v1/ready
GET  /v1/routes
GET  /v1/routes/{route_id}
GET  /v1/routes/{route_id}/stations
GET  /v1/stations
GET  /v1/vehicles
GET  /v1/vehicles/{vehicle_id}
POST /v1/telemetry
GET  /v1/alerts
POST /v1/incidents
```

`GET /v1/vehicles/{id}` deriva online/offline, estabiliza el sentido con historial y calcula próxima estación/ETA en backend.

`POST /v1/telemetry` es idempotente por `(device_id, seq)` y valida coordenadas, timestamp, velocidad, precisión, heading y satélites.

## Autenticación

```text
Authorization: Device <token>
Authorization: Driver <token>
```

Los tokens persistidos se guardan como SHA-256.

## Tests

```bash
python -m compileall -q backend
python -m unittest discover -s backend/tests -v
```

GitHub Actions ejecuta los tests contra PostgreSQL + PostGIS antes del deploy.

Contrato completo: `contracts/api_v1.md`.
