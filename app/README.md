# Zentryx · interfaz móvil

## Ejecutar

```bash
cd app
source .venv/bin/activate
flet run --web main.py
```

Para abrirla en un teléfono de la misma red:

```bash
flet run --web --host '*' --port 8550 main.py
```

## Modo demo y modo API real

Sin variables adicionales, la app usa `VehicleService` como fuente de demostración.

Para consumir la API real:

```bash
export ZENTRYX_API_BASE_URL="http://127.0.0.1:5000"
export ZENTRYX_SERVICE_ID="l2-ordinary"
export ZENTRYX_VEHICLE_ID="unit-01"
flet run --web main.py
```

En modo API:

- `GET /v1/routes` selecciona el servicio por `ZENTRYX_SERVICE_ID`;
- `GET /v1/routes/{id}` carga la geometría real desde PostgreSQL/PostGIS;
- `GET /v1/routes/{id}/stations` carga estaciones y `stop_order`;
- `GET /v1/vehicles/{id}` alimenta posición, heading, estado y navegación;
- `GET /v1/alerts` alimenta el banner de avisos reales;
- próxima estación y ETA vienen únicamente del backend;
- `direction=unknown` ya no se convierte artificialmente en ida;
- si la API está caída desde el arranque, la app muestra estado sin conexión y oculta el marcador hasta conocer una posición real;
- si se pierde conexión después de recibir una posición, conserva la última ubicación y marca la unidad como offline.

Si la API no puede entregar la definición de ruta durante el arranque, el mapa puede usar el asset local como fallback visual, mientras el adaptador de vehículo sigue intentando conectar al backend.

## Organización

- `main.py`: pantalla, mapa, cámara y selección demo/API.
- `components/passenger.py`: tarjeta de pasajero, cabecera y alertas.
- `services/route_service.py`: catálogo/validación local.
- `services/api_route_service.py`: definición de ruta y estaciones desde API.
- `services/vehicle_service.py`: geometría y simulación local.
- `services/api_vehicle_service.py`: unidad real por REST.
- `services/api_alert_service.py`: alertas activas por REST.
- `assets/routes/`: fallback local y datos de desarrollo.

## Línea 2 local

```text
assets/routes/
├── l2_ordinary_route.geojson
├── l2_ordinary_stations.geojson
└── l2_express_ero.geojson
```

El servicio ordinario conserva 43 estaciones ordenadas de La Quebrada a Las Américas. ERO permanece separado como dato de servicio exprés.

## Seguimiento del mapa

El marcador actualiza cada snapshot; la cámara se limita por tiempo y distancia para evitar jitter. Mover el mapa activa **Exploración libre** y el botón de centrado reactiva seguimiento. La rotación del heading evita la vuelta larga al cruzar 0°/360°.

## Validación

```bash
python -m unittest discover -s tests -v
python -m compileall -q main.py components services theme.py
```

Las pruebas cubren UI, cámara, heading, rutas locales, adaptadores API, `direction=unknown`, arranque offline, carga de rutas desde contrato y alertas.

La especificación del backend está en `../contracts/api_v1.md` y el esquema en `../BD/database_v1.sql`.
