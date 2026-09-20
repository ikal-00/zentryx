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

## Organización del frontend

- `main.py`: composición de pantalla, cámara, selección de estaciones y consumo del adaptador de vehículo.
- `components/passenger.py`: cabecera, controles, tarjeta de unidad/estación y banner de alertas.
- `services/route_service.py`: catálogo y validación de líneas/servicios/rutas.
- `services/vehicle_service.py`: contrato actual de snapshots y fuente de demostración.
- `theme.py`: colores, dimensiones, sombras y configuración de Flet.
- `assets/routes/`: geometría y estaciones separadas por servicio.

### Assets actuales

```text
assets/routes/
├── l2_ordinary_route.geojson
├── l2_ordinary_stations.geojson
└── l2_express_ero.geojson
```

`l2_ordinary_route.geojson` contiene el corredor La Quebrada → Las Américas reconstruido a partir de los `ways` de la relación OSM de Línea 2. La polilínea se recortó a las terminales y se simplificó con una desviación máxima aproximada de 1.5 m para conservar detalle sin cargar cientos de vértices innecesarios.

`l2_ordinary_stations.geojson` mantiene las 43 estaciones del servicio ordinario con `stop_order` de 1 a 43. El frontend usa ese orden como fuente de verdad; la proyección sobre la geometría se utiliza únicamente para obtener progreso métrico mientras siga activo el adaptador de demostración.

ERO queda separado porque corresponde al servicio exprés y no se inserta artificialmente dentro de la secuencia del servicio ordinario.

## Preparado para múltiples servicios

La UI ya no necesita conocer nombres como `La Quebrada` o `Las Américas` dentro de `VehicleService`. `route_service.py` entrega:

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

El marcador del vehículo continúa actualizándose con cada snapshot, pero la cámara ya no intenta iniciar una animación por cada pequeño grupo de paquetes. El seguimiento se limita por tiempo y distancia mínima, reduciendo animaciones solapadas.

Mover el mapa manualmente cambia a **Exploración libre**. El botón de centrar vuelve a la última posición de la unidad y reactiva el seguimiento.

La rotación del marcador usa un ángulo continuo para evitar que un cambio de heading como `359° → 1°` provoque visualmente una vuelta casi completa.

## Datos actuales y futura API

`VehicleService` sigue siendo únicamente una fuente de demostración hasta que esté disponible la API. La UI muestra **Datos de demostración** y no afirma que la unidad sea GPS en vivo.

No se agregaron saturación, alertas, incidentes ni unidades ficticias nuevas.

La próxima estación y el ETA siguen calculándose localmente solo para mantener funcional la demo. Cuando el backend entregue esos datos, la app debe consumirlos y retirar ese cálculo local para evitar dos fuentes de verdad.

El siguiente adaptador real debería conservar, en lo posible, el contrato de `VehicleSnapshot` para que `main.py` no tenga que reconstruirse.

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
- ETA en ambos sentidos de la demo
- `stop_order` 1–43 sin huecos
- nombres de estación sin duplicados
- terminales correctas
- estaciones alineadas a menos de 30 m de la geometría
- inyección de etiquetas de dirección sin hardcodes de Línea 2
- tamaños de ventana móvil, landscape y escritorio

Backend, BD, firmware y contratos API permanecen fuera de estos cambios.
