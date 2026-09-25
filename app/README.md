# Zentryx · interfaz móvil

## Ejecutar

Desde la raíz del repositorio, con el entorno existente:

```bash
cd app
source .venv/bin/activate
flet run --web main.py
```

Si falta alguna dependencia:

```bash
python -m pip install -r requirements.txt
```

Para abrirla en un teléfono conectado a la misma red local:

```bash
flet run --web --host '*' --port 8550 main.py
```

Los mosaicos de OpenStreetMap necesitan conexión a internet.

## Modo demo y modo API real

Sin variables adicionales, la app conserva `VehicleService` como fuente de demostración para poder desarrollar la UI sin depender del backend.

Para consumir la API real:

```bash
export ZENTRYX_API_BASE_URL="http://127.0.0.1:5000"
export ZENTRYX_VEHICLE_ID="unit-01"
flet run --web main.py
```

`ApiVehicleService` consulta `GET /v1/vehicles/{vehicle_id}` aproximadamente cada segundo y conserva la misma interfaz de snapshots que usa el mapa. Cuando este modo está activo:

- la posición, velocidad, heading, ocupación y estado vienen del backend;
- el estado `online/offline/unknown` usa la frescura calculada por la API;
- próxima estación, distancia restante y ETA vienen de `navigation` del backend;
- el frontend deja de calcular el ETA de producción por su cuenta.

Si la API deja de responder temporalmente y ya existe una posición conocida, el adaptador conserva esa última posición y la presenta como `offline`.

## Organización del frontend

- `main.py`: composición de pantalla, cámara, selección de estaciones y selección del adaptador demo/API.
- `components/passenger.py`: cabecera, controles, tarjeta de unidad/estación y banner de alertas.
- `services/route_service.py`: catálogo y validación de líneas/servicios/rutas.
- `services/vehicle_service.py`: geometría, contrato de snapshots y fuente de demostración.
- `services/api_vehicle_service.py`: adaptador REST para datos reales de unidades.
- `theme.py`: colores, dimensiones, sombras y configuración de Flet.
- `assets/routes/`: geometría y estaciones separadas por servicio.

### Assets actuales

```text
assets/routes/
├── l2_ordinary_route.geojson
├── l2_ordinary_stations.geojson
└── l2_express_ero.geojson
```

`l2_ordinary_route.geojson` contiene el corredor La Quebrada → Las Américas reconstruido a partir de los `ways` de la relación OSM de Línea 2.

`l2_ordinary_stations.geojson` mantiene las 43 estaciones del servicio ordinario con `stop_order` de 1 a 43. El frontend usa ese orden como fuente de verdad.

ERO queda separado porque corresponde al servicio exprés y no se inserta artificialmente dentro de la secuencia del servicio ordinario.

## Preparado para múltiples servicios

La UI no necesita conocer nombres como `La Quebrada` o `Las Américas` dentro de `VehicleService`. `route_service.py` entrega:

- `route_id`
- `line_id`
- etiqueta de línea
- red
- `service_id`
- nombre de servicio
- terminal origen/destino
- etiquetas de ambos sentidos
- geometría
- estaciones ordenadas

Para añadir otra variante se agregan sus assets y una entrada en `SERVICE_ASSETS`; el mapa puede reutilizar la misma estructura.

## Seguimiento del mapa

El marcador del vehículo se actualiza con cada snapshot, pero la cámara se limita por tiempo y distancia mínima para evitar animaciones solapadas.

Mover el mapa manualmente cambia a **Exploración libre**. El botón de centrar vuelve a la última posición de la unidad y reactiva el seguimiento.

La rotación del marcador usa un ángulo continuo para evitar que un cambio de heading como `359° → 1°` provoque visualmente una vuelta casi completa.

## Validación

Desde `app`:

```bash
python -m unittest discover -s tests -v
python -m compileall -q main.py components services theme.py
```

Las pruebas cubren, entre otras cosas:

- seguimiento y exploración libre
- botón de centrado
- selección de estaciones
- limitación de movimientos de cámara ante ráfagas de snapshots
- heading al cruzar 0°/360°
- ETA de la demo en ambos sentidos
- `stop_order` 1–43 sin huecos
- nombres de estación sin duplicados
- terminales correctas
- estaciones alineadas a la geometría
- inyección de etiquetas de dirección sin hardcodes de Línea 2
- tamaños de ventana móvil, landscape y escritorio

La especificación del backend vive en `../contracts/api_v1.md` y el esquema en `../BD/database_v1.sql`.
