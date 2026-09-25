# Zentryx backend · API v1

## Preparar entorno

Desde la raíz del repositorio:

```bash
cd backend
pipenv install
```

La API necesita `POSTGRES_URL` apuntando a PostgreSQL + PostGIS.

```text
POSTGRES_URL=postgresql://user:password@localhost:5432/zentryx
DB_POOL_MIN=1
DB_POOL_MAX=10
HOST=0.0.0.0
PORT=5000
```

## Base de datos

Base nueva:

```bash
psql "$POSTGRES_URL" -f BD/database_v1.sql
```

Base existente:

```bash
psql "$POSTGRES_URL" -f BD/migrations/002_api_alignment.sql
psql "$POSTGRES_URL" -f BD/migrations/003_runtime_hardening.sql
```

Carga de la Línea 2 ordinaria desde los GeoJSON reales del frontend:

```bash
POSTGRES_URL="$POSTGRES_URL" python -m backend.seed_routes
```

`BD/Gps_sql/Gps_sql.sql` está deprecado.

## Servidor compartido con Docker

La instalación compartida usa `docker-compose.yml` en la raíz y levanta PostgreSQL/PostGIS y la API en contenedores separados. La base queda en el volumen persistente `zentryx_db` y PostgreSQL no publica el puerto 5432 al host.

Crea un `.env` local a partir de `.env.example`. `POSTGRES_PASSWORD` debe ser un valor aleatorio y `API_BIND_IP` debe ser la IP Tailscale del servidor. `.env` está ignorado por Git.

```bash
cp .env.example .env
# Editar .env antes de arrancar.
docker compose up -d --build
```

La API carga/actualiza el seed de Línea 2 al arrancar y se sirve con Gunicorn. Para comprobar el servidor:

```bash
docker compose ps
curl http://<TAILSCALE_IP>:5000/v1/health
curl http://<TAILSCALE_IP>:5000/v1/ready
curl http://<TAILSCALE_IP>:5000/v1/routes
```

Para desplegar cambios nuevos del repositorio:

```bash
git pull --ff-only origin main
docker compose up -d --build
```

No uses `docker compose down -v` salvo que quieras borrar deliberadamente la base de datos de desarrollo.

## Tokens

Dispositivos GPS:

```text
Authorization: Device <token>
```

Conductores que reportan incidentes:

```text
Authorization: Driver <token>
```

Ambos tokens se almacenan como SHA-256 (`sha256:<64 hex>`), nunca en texto plano.

## Ejecutar sin Docker

Desde la raíz:

```bash
python -m backend.API_Global
```

Liveness:

```bash
curl http://127.0.0.1:5000/v1/health
```

Readiness real de PostgreSQL/PostGIS:

```bash
curl http://127.0.0.1:5000/v1/ready
```

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

`GET /v1/vehicles/{id}` deriva estado online/offline, usa varias muestras recientes para estabilizar el sentido y calcula próxima estación/ETA en backend. El ETA usa velocidad suavizada reciente y la velocidad por defecto de la ruta como fallback cuando la unidad está detenida.

## Telemetría

`POST /v1/telemetry` es idempotente por `(device_id, seq)`. Valida schema, coordenadas, timestamp, velocidad, precisión, heading y satélites. También rechaza timestamps con más de 5 minutos de futuro o más de 24 horas de antigüedad.

## Incidentes

Un incidente requiere un conductor activo en `drivers` y una asignación activa en `driver_vehicle_assignments`. Ya no se comparte el token físico del GPS con la interfaz del conductor.

## Tests

```bash
python -m compileall -q backend
python -m unittest discover -s backend/tests -v
```

GitHub Actions levanta un contenedor real PostgreSQL + PostGIS y prueba el ciclo completo: esquema → seed L2 → telemetría → unidad/navegación → alertas → incidente de conductor.

El contrato completo está en `contracts/api_v1.md`.
