# Paridad móvil

Estado del cliente Flutter frente al MVP de pasajero en Flet.

## Paridad funcional alcanzada en código

- Mapa OpenStreetMap.
- Geometría real de Mexibús Línea 2 desde `/v1/routes/{route_id}`.
- Estaciones reales desde `/v1/routes/{route_id}/stations`.
- Explorador de ruta y lista de estaciones.
- Selección y centrado de estaciones.
- Unidad `unit-demo-01` consumida desde la API compartida.
- Posición, heading, velocidad y estado online/offline.
- Próxima estación, distancia restante y ETA calculados por backend.
- Ocupación cuando el backend disponga del dato.
- Alertas activas.
- Seguimiento automático de la unidad.
- Desactivación del seguimiento cuando el usuario explora el mapa.
- Botón para volver a centrar la unidad.
- Interpolación visual de posición y heading entre muestras.
- Conservación del último estado válido durante una caída de red.
- Polling pausado en segundo plano y refresh al volver.
- Dark mode dinámico y superficies Cupertino/Zentryx.
- Accesibilidad básica mediante `Semantics` en controles y estaciones.

## Validación automatizada

`Zentryx Mobile CI` ejecuta:

- `flutter analyze`
- `flutter test`
- build Android debug
- build iOS simulator
- publicación temporal de ambos artefactos de prueba

El backend y el contrato `/v1` no cambian por esta migración.

## Gate antes de retirar Flet

La paridad de implementación y build puede validarse automáticamente, pero retirar `app/` requiere una prueba manual corta en hardware real:

1. Abrir la app en al menos un iPhone y un Android.
2. Confirmar acceso a `100.72.215.34:5000` con Tailscale conectado.
3. Recorrer mapa, estaciones, seguimiento, alertas y modo offline.
4. Confirmar que no hay problemas de safe areas, gestos o consumo anormal.

Hasta completar ese gate, `app/` permanece como cliente de respaldo. No bloquea el uso ni el desarrollo de `mobile/`.
