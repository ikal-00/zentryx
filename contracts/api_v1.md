# Zentryx API Contract v1

Este documento define cómo la app, el backend y el GPS se comunican entre sí. El contrato es independiente del framework del backend.

## Convenciones generales

- Base path: `/v1`
- Formato: JSON
- `Content-Type` para bodies JSON: `application/json`
- Timestamps: ISO 8601 con zona horaria; el backend normaliza a UTC
- IDs públicos: strings legibles (`unit-01`, `gps-01`, `route-l2`)
- Coordenadas: WGS84 (`lat`, `lon`)
- Los clientes nunca acceden directamente a PostgreSQL
- Los tokens de dispositivo se guardan como SHA-256, formato `sha256:<hex>`

Errores JSON usan al menos:

```json
{"error": "error_code"}
```

Los errores de validación pueden añadir `field` y `detail`.

## 1. Salud del backend

### GET `/v1/health`

Respuesta 200:

```json
{"status": "ok"}
```

## 2. Rutas y servicios

Una ruta puede representar una variante/servicio concreto de una línea. Esto permite tener, por ejemplo, servicio ordinario, exprés o ramales sin asumir que una línea equivale a un solo recorrido.

### GET `/v1/routes`

Respuesta 200:

```json
{
  "routes": [
    {
      "route_id": "route-l2",
      "name": "Mexibús Línea 2",
      "active": true,
      "line_id": "mexibus-l2",
      "line_label": "L2",
      "service_id": "l2-ordinary",
      "service_name": "Servicio ordinario",
      "origin_name": "La Quebrada",
      "destination_name": "Las Américas",
      "direction_forward_label": "La Quebrada → Las Américas",
      "direction_reverse_label": "Las Américas → La Quebrada"
    }
  ]
}
```

Los campos de metadatos pueden ser `null` mientras una ruta antigua no haya sido migrada.

### GET `/v1/routes/{route_id}/stations`

Respuesta 200:

```json
{
  "route_id": "route-l2",
  "stations": [
    {
      "station_id": "station-bandera-tultitlan",
      "name": "Bandera Tultitlán",
      "position": {
        "lat": 19.62211,
        "lon": -99.16299
      },
      "active": true,
      "order": 9
    }
  ]
}
```

Ruta inexistente: 404 `route_not_found`.

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

Devuelve `{"vehicles": [...]}` con el mismo formato de unidad que el endpoint individual.

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
  "occupancy_level": "unknown",
  "last_update": "2026-09-20T05:31:22Z",
  "navigation": {
    "direction": "forward",
    "direction_label": "La Quebrada → Las Américas",
    "progress_m": 3250.2,
    "route_length_m": 22193.9,
    "next_station": {
      "station_id": "station-bandera-tultitlan",
      "name": "Bandera Tultitlán"
    },
    "distance_remaining_m": 184.6,
    "eta_seconds": 22.2
  }
}
```

`navigation` puede ser `null` si la ruta no tiene geometría/estaciones suficientes. `direction` puede ser `unknown` hasta disponer de al menos dos posiciones con movimiento suficiente. En terminal, `next_station` es `null`, `distance_remaining_m` es `0` y `eta_seconds` es `0`.

Estados iniciales:

- `online`: última telemetría recibida hace 30 segundos o menos
- `offline`: existe telemetría, pero está vencida
- `unknown`: nunca se ha recibido telemetría

Niveles de ocupación:

- `low`
- `medium`
- `high`
- `unknown`

## 5. Telemetría enviada por GPS

### POST `/v1/telemetry`

Headers:

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

Duplicado por `(device_id, seq)`:

```json
{
  "accepted": true,
  "duplicate": true,
  "device_id": "gps-01",
  "seq": 152
}
```

Validaciones relevantes:

- `schema_version` debe ser `1`
- `seq` debe ser entero >= 0
- latitud entre -90 y 90
- longitud entre -180 y 180
- `speed_mps` y `accuracy_m` >= 0 cuando existan
- `heading_deg` entre 0 (incluido) y 360 (excluido)
- `satellites` entero >= 0 cuando exista
- `observed_at` debe incluir zona horaria

Códigos importantes:

- 202: aceptado o duplicado idempotente
- 400: JSON/Content-Type inválido
- 401: token inválido
- 404: dispositivo o unidad inexistente/inactiva
- 422: datos inválidos
- 500: error interno
- 503: PostgreSQL no disponible

## 6. Alertas

### GET `/v1/alerts`

Parámetros opcionales: `route_id` y `vehicle_id`. Una alerta `active=true` se mantiene visible aunque haya sido creada un día anterior, hasta que sea resuelta/desactivada.

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

Severidades: `info`, `warning`, `critical`.

## 7. Incidentes reportados por conductor

### POST `/v1/incidents`

Para el MVP la interfaz del conductor autoriza la acción con la credencial `Device` de la unidad asignada. No se expone ninguna credencial de PostgreSQL al cliente. Cuando exista autenticación propia de conductores, deberá versionarse o ampliarse este esquema sin romper v1.

Headers:

```text
Content-Type: application/json
Authorization: Device <token>
```

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
  "incident_id": "incident-a1b2c3d4e5f6",
  "created": true
}
```

## 8. Tiempo real

Para el MVP la app puede usar REST. Más adelante:

### WebSocket `/v1/realtime`

Eventos previstos:

- `vehicle.position.updated`
- `vehicle.occupancy.updated`
- `alert.created`
- `incident.created`

## Flujo principal

```text
GPS / C++
    |
    | POST /v1/telemetry
    v
Backend Flask
    |
    v
PostgreSQL + PostGIS
    |
    | GET /v1/vehicles/{id}
    v
App Flet
```

Este archivo es el contrato funcional v1. Si cambia un campo que rompe compatibilidad, se debe crear una nueva versión en lugar de modificar silenciosamente el formato usado por los clientes.
