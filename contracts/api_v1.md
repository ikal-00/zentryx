# Zentryx API Contract v1

Contrato entre app móvil de pasajero, backend y telemetría GPS.

## Convenciones generales

- Base path: `/v1`
- JSON: `Content-Type: application/json`
- Timestamps: ISO 8601 con zona horaria; el backend normaliza a UTC
- Coordenadas: WGS84 (`lat`, `lon`)
- IDs públicos: strings legibles
- Los clientes nunca acceden directamente a PostgreSQL
- Tokens persistidos: SHA-256, formato `sha256:<hex>`
- Errores JSON: `{"error":"error_code"}`; validación puede añadir `field` y `detail`

## 1. Salud y readiness

### GET `/v1/health`

Liveness del proceso Flask, sin consultar la BD.

```json
{"status":"ok"}
```

### GET `/v1/ready`

Comprueba PostgreSQL y PostGIS. Respuesta 200:

```json
{"status":"ready","database":"ok","postgis_version":"3.x"}
```

Si la dependencia no está disponible: 503.

## 2. Rutas y servicios

Una línea puede tener varias rutas/servicios. `service_id` identifica la variante concreta y es único; el nombre comercial de la línea puede repetirse.

### GET `/v1/routes`

Por defecto devuelve rutas activas. `?active=false` incluye también inactivas.

```json
{
  "routes": [{
    "route_id":"route-l2",
    "name":"Mexibús Línea 2 · Servicio ordinario",
    "active":true,
    "line_id":"mexibus-l2",
    "line_label":"L2",
    "network_name":"Mexibús",
    "service_id":"l2-ordinary",
    "service_name":"Servicio ordinario",
    "origin_name":"La Quebrada",
    "destination_name":"Las Américas",
    "direction_forward_label":"La Quebrada → Las Américas",
    "direction_reverse_label":"Las Américas → La Quebrada",
    "default_speed_mps":6.0
  }]
}
```

### GET `/v1/routes/{route_id}`

Devuelve los mismos metadatos y la geometría del recorrido como puntos `lat/lon`:

```json
{
  "route_id":"route-l2",
  "service_id":"l2-ordinary",
  "path":[
    {"lat":19.59184,"lon":-99.18812},
    {"lat":19.59223,"lon":-99.18769}
  ]
}
```

Ruta inexistente/inactiva: 404 `route_not_found`.

### GET `/v1/routes/{route_id}/stations`

```json
{
  "route_id":"route-l2",
  "stations":[{
    "station_id":"node/4332377599",
    "name":"Bandera Tultitlán",
    "position":{"lat":19.6220699,"lon":-99.1629897},
    "active":true,
    "order":9
  }]
}
```

### GET `/v1/stations`

Devuelve todas las estaciones activas con `station_id`, `name`, `position` y `active`.

## 3. Unidades

### GET `/v1/vehicles`

Devuelve `{"vehicles":[...]}`.

### GET `/v1/vehicles/{vehicle_id}`

```json
{
  "vehicle_id":"unit-01",
  "route_id":"route-l2",
  "status":"online",
  "position":{"lat":19.62211,"lon":-99.16299},
  "speed_mps":8.3,
  "accuracy_m":4.7,
  "heading_deg":124.5,
  "occupancy_level":"unknown",
  "last_update":"2026-09-25T20:31:22Z",
  "navigation":{
    "direction":"forward",
    "direction_source":"history",
    "direction_label":"La Quebrada → Las Américas",
    "progress_m":3250.2,
    "route_length_m":22193.9,
    "next_station":{"station_id":"node/4332377599","name":"Bandera Tultitlán"},
    "distance_remaining_m":184.6,
    "eta_seconds":24.4,
    "eta_speed_mps":7.57
  }
}
```

`direction_source` puede ser `history`, `heading` o `null`. El backend usa varias muestras recientes para evitar que el ruido GPS cambie el sentido. Si el movimiento no basta, puede usar heading respecto al recorrido. `eta_speed_mps` usa velocidad suavizada reciente y, si no hay velocidad útil, `default_speed_mps` de la ruta para evitar que el ETA desaparezca en una parada corta.

Estados:
- `online`: última telemetría <= 30 s
- `offline`: hay telemetría pero está vencida
- `unknown`: no hay telemetría

## 4. Telemetría GPS

### POST `/v1/telemetry`

Headers:

```text
Content-Type: application/json
Authorization: Device <token>
```

Body:

```json
{
  "schema_version":1,
  "device_id":"gps-01",
  "vehicle_id":"unit-01",
  "seq":152,
  "observed_at":"2026-09-25T20:31:22Z",
  "position":{
    "lat":19.62211,
    "lon":-99.16299,
    "speed_mps":8.3,
    "accuracy_m":4.7,
    "heading_deg":124.5,
    "satellites":12
  }
}
```

Respuesta: 202. `(device_id, seq)` es idempotente y un duplicado responde `duplicate:true`.

Validaciones:
- `schema_version == 1`
- `seq` entero >= 0
- latitud [-90,90], longitud [-180,180]
- speed/accuracy >= 0
- heading [0,360)
- satellites entero >= 0
- timestamp con zona horaria
- `observed_at` no puede estar más de 5 min en el futuro ni más de 24 h en el pasado

## 5. Alertas

### GET `/v1/alerts`

Parámetros opcionales: `route_id`, `vehicle_id`. Solo devuelve alertas activas; prioridad `critical`, `warning`, `info`, y luego más recientes.

```json
{
  "alerts":[{
    "alert_id":"alert-001",
    "route_id":"route-l2",
    "vehicle_id":null,
    "type":"service",
    "message":"Servicio con retraso",
    "severity":"warning",
    "created_at":"2026-09-25T20:20:00Z",
    "active":true
  }]
}
```

## 6. Códigos relevantes

- 200: lectura correcta
- 202: telemetría aceptada/duplicada
- 400: JSON o Content-Type inválido
- 401: credencial inválida
- 404: recurso/asignación inexistente
- 422: payload inválido
- 500: error interno
- 503: dependencia no disponible / backend no ready

## 7. Tiempo real

El MVP usa REST. Futuro WebSocket `/v1/realtime` con eventos de posición, ocupación y alertas.

Este archivo es el contrato funcional v1. Cambios incompatibles requieren una nueva versión.
