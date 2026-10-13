# Navegación y experiencia del pasajero

## Flujo de navegación

La aplicación móvil de Zentryx está enfocada exclusivamente en la experiencia del pasajero del sistema Mexibús.

Un único Navigator Cupertino gestiona la navegación:
* `/` (Bienvenida / Introducción): Presenta la marca, estado y acceso directo al mapa interactivo.
* `/passenger` (`HomeScreen`): Vista principal del pasajero con cartografía interactiva de la Línea 2 del Mexibús, seguimiento en vivo de unidades, estado de estaciones, cálculo de tiempos de llegada (ETA) y HUD de estado del servicio.

## Arquitectura de la vista del pasajero

* **Cartografía interactiva:** Basada en `flutter_map` con soporte para selección de estaciones, seguimiento de vehículo y controles fluidos de cámara.
* **Telemetría y movimiento:** `vehicle_motion` interpola posiciones GPS y rumbos (heading) eliminando saltos bruscos y jitter para un seguimiento suave en tiempo real.
* **HUD y hojas informativas:** Paneles compactos y no intrusivos que presentan la próxima estación, tiempo estimado de llegada, estado de la conexión y alertas del servicio.
