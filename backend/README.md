# Zentryx backend · API v1

## Preparar entorno

Desde la raíz del repositorio:

```bash
cd backend
pipenv install
```

La API necesita `POSTGRES_URL` apuntando a PostgreSQL + PostGIS.

Ejemplo `.env` local:

```text
POSTGRES_URL=postgresql://user:password@localhost:5432/zentryx
DB_POOL_MIN=1
DB_POOL_MAX=10
HOST=0.0.0.0
PORT=5000
```

## Base de datos

Para una base nueva ejecuta:

```bash
psql "$POSTGRES_URL" -f ../BD/database_v1.sql
```

Si la base ya existía antes de añadir metadatos de línea/servicio, ejecuta además:

```bash
psql "$POSTGRES_URL" -f ../BD/migrations/002_api_alignment.sql
```

`BD/Gps_sql/Gps_sql.sql` está deprecado y no debe utilizarse.

## Tokens de dispositivo

La columna `devices.token_hash` guarda SHA-256, no el token plano.

Para generar un valor:

```bash
python -c "import hashlib; t='TU_TOKEN'; print('sha256:'+hashlib.sha256(t.encode()).hexdigest())"
```

El GPS envía el token original:

```text
Authorization: Device TU_TOKEN
```

## Ejecutar

Desde la raíz del repositorio:

```bash
python -m backend.API_Global
```

Health check:

```bash
curl http://127.0.0.1:5000/v1/health
```

Respuesta esperada:

```json
{"status":"ok"}
```

## Endpoints MVP

```text
GET  /v1/health
GET  /v1/routes
GET  /v1/routes/{route_id}/stations
GET  /v1/stations
GET  /v1/vehicles
GET  /v1/vehicles/{vehicle_id}
POST /v1/telemetry
GET  /v1/alerts
POST /v1/incidents
```

`GET /v1/vehicles/{id}` devuelve además `navigation`, calculado en el backend: sentido, progreso, próxima estación, distancia restante y ETA simple por distancia/velocidad.

## Telemetría

`POST /v1/telemetry` es idempotente por `(device_id, seq)`. Un paquete nuevo se inserta; un paquete repetido devuelve `duplicate: true` sin crear otra fila.

La API valida schema, coordenadas, timestamp, velocidad, precisión, heading y satélites antes de tocar PostgreSQL.

## Estado online/offline

La respuesta de unidades deriva el estado de `last_update`:

- `online`: telemetría de hace 30 s o menos
- `offline`: existe telemetría pero está vencida
- `unknown`: nunca se ha recibido telemetría

## Tests

Desde la raíz:

```bash
python -m compileall -q backend
python -m unittest discover -s backend/tests -v
```

También existe `.github/workflows/backend-api.yml` para ejecutar estas comprobaciones en GitHub Actions.

El contrato completo está en `contracts/api_v1.md`.
