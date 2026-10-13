# Contratos

La interfaz pública es HTTP `/v1`; los imports Python y tablas son internos.

| Recurso | Request | Response |
| --- | --- | --- |
| Salud | GET `/v1/health`, `/v1/ready` | Estado proceso/DB |
| Rutas | GET `/v1/routes`, detalle y estaciones | Metadatos y geometría WGS84 |
| Unidades | GET `/v1/vehicles`, detalle | Posición, estado y navegación |
| Telemetría | POST `/v1/telemetry`, auth Device | 202, aceptación idempotente |
| Alertas | GET `/v1/alerts`, filtros opcionales | Alertas ordenadas |

[api_v1.md](api_v1.md) define campos, respuestas y errores. [telemetry_v1.json](telemetry_v1.json) es un ejemplo, no un JSON Schema ni un evento para reenviar con fecha antigua.

No hay WebSocket implementado. Cambios incompatibles requieren otra versión; cambios compatibles actualizan servidor, consumidores y pruebas. `route-l2` identifica ruta; `l2-ordinary`, servicio; `unit-demo-01`, unidad compartida demo.
