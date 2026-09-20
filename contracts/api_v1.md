# Zentryx API Contract v1

Este documento define cómo la app, el backend y el GPS se comunican entre sí. El contrato es independiente de si el backend termina implementándose con Flask o FastAPI.

## Convenciones generales

- Base path: `/v1`
- Formato: JSON
- Timestamps: ISO 8601 en UTC, por ejemplo `2026-09-20T05:30:00Z`
- IDs públicos: strings legibles (`unit-01`, `gps-01`, `route-l2`)
- Coordenadas: WGS84 (`lat`, `lon`)
- Los clientes nunca acceden directamente a PostgreSQL.

## 1. Salud del backend

### GET `/v1/health`

Respuesta 200:

```json
{
  "status": "ok"
}
```

## 2. Rutas

### GET `/v1/routes`

Respuesta 200:

```json
{
  "routes": [
    {
      "route_id": "route-l2",
      "name": "Mexibús Línea 2",
      "active": true
    }
  ]
}
```

### GET `/v1/routes/{route_id}/stations`

Respuesta 200:

```json
{
  "route_id": "route-l2",
  "stations": [
    {
      "station_id": "station-bandera-tultitlan",
      "name": "Bandera Tultitlán",
      "order": 1,
      "position": {
        "lat": 19.62211,
        "lon": -99.16299
      }
    }
  ]
}
```

## 3. Estaciones

### GET `/v1/stations`

Respuesta 200:

```json
{
  "stations": [
    {
      "station_id": "station-bandera-tultitlan",
      "name": "Bandera Tultitlán",
      "position": {
        "lat": 19.62211,
        "lon": -99.16299
      },
      "active": true
    }
  ]
}
```

## 4. Unidades

### GET `/v1/vehicles`

Respuesta 200:

```json
{
  "vehicles": [
    {
      "vehicle_id": "unit-01",
      "route_id": "route-l2",
      "status": "online",
      "position": {
        "lat": 19.62211,
        "lon": -99.16299
      },
      "speed_mps": 8.3,
      "accuracy_m": 4.7,
      "heading_deg": 124.5,
      "occupancy_level": "medium",
      "last_update": "2026-09-20T05:31:22Z"
    }
  ]
}
```

### GET `/v1/vehicles/{vehicle_id}`

Respuesta 200:

```json
{
  "vehicle_id": "unit-01",
  "route_id": "route-l2",
  "status": "online",
  "position": {
    "lat": 19.62211,
    "lon": -99.16299
  },
  "speed_mps": 8.3,
  "accuracy_m": 4.7,
  "heading_deg": 124.5,
  "occupancy_level": "medium",
  "last_update": "2026-09-20T05:31:22Z"
}
```

Estados iniciales de unidad:

- `online`
- `offline`
- `unknown`

Niveles iniciales de ocupación:

- `low`
- `medium`
- `high`
- `unknown`

## 5. Telemetría enviada por GPS

### POST `/v1/telemetry`

Header esperado:

```text
Content-Type: application/json
Authorization: Device <token>
```

Body:

```json
{
  "schema_version": 1,
  "device_id": "gps-01",
  "vehicle_id": "unit-01",
  "seq": 152,
  "observed_at": "2026-09-20T05:31:22Z",
  "position": {
    "lat": 19.62211,
    "lon": -99.16299,
    "speed_mps": 8.3,
    "accuracy_m": 4.7,
    "heading_deg": 124.5,
    "satellites": 12
  }
}
```

Respuesta 202:

```json
{
  "accepted": true,
  "device_id": "gps-01",
  "seq": 152
}
```

Si el paquete ya había sido recibido:

```json
{
  "accepted": true,
  "duplicate": true,
  "device_id": "gps-01",
  "seq": 152
}
```

Códigos importantes:

- 202: aceptado
- 400: JSON mal formado
- 401: token inválido
- 404: dispositivo o unidad inexistente
- 422: datos inválidos
- 500/503: error temporal del servidor

## 6. Alertas

### GET `/v1/alerts`

Respuesta 200:

```json
{
  "alerts": [
    {
      "alert_id": "alert-001",
      "route_id": "route-l2",
      "vehicle_id": null,
      "type": "service",
      "message": "Servicio con retraso",
      "severity": "warning",
      "created_at": "2026-09-20T05:20:00Z",
      "active": true
    }
  ]
}
```

Severidades iniciales:

- `info`
- `warning`
- `critical`

## 7. Incidentes reportados por conductor

### POST `/v1/incidents`

Body:

```json
{
  "vehicle_id": "unit-01",
  "type": "traffic",
  "description": "Congestión intensa en el corredor",
  "position": {
    "lat": 19.62211,
    "lon": -99.16299
  },
  "observed_at": "2026-09-20T05:35:00Z"
}
```

Respuesta 201:

```json
{
  "incident_id": "incident-001",
  "created": true
}
```

## 8. Tiempo real

Para el MVP, la app puede empezar usando REST.

Más adelante:

### WebSocket `/v1/realtime`

Eventos previstos:

- `vehicle.position.updated`
- `vehicle.occupancy.updated`
- `alert.created`
- `incident.created`

Ejemplo:

```json
{
  "event": "vehicle.position.updated",
  "data": {
    "vehicle_id": "unit-01",
    "position": {
      "lat": 19.62211,
      "lon": -99.16299
    },
    "last_update": "2026-09-20T05:31:22Z"
  }
}
```

## Flujo principal

```text
GPS / C++
    |
    | POST /v1/telemetry
    v
Backend
    |
    v
PostgreSQL + PostGIS
    |
    | GET /v1/vehicles/{id}
    v
App Flet
```

Este archivo es el contrato funcional v1. Si cambia un campo que rompe compatibilidad, se debe crear una nueva versión del contrato en lugar de modificar silenciosamente el formato usado por los clientes.
