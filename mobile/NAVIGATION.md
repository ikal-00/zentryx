# Inicio, navegación y conductor

`ZentryxApp` conserva `ProviderScope`, Cupertino y el observador de lifecycle.
`AppRoutes` usa un único Navigator y `CupertinoPageRoute`: `/` (bienvenida),
`/passenger` (HomeScreen existente), `/driver` (dashboard local). No se añade
ninguna dependencia ni se inicia la API al abrir bienvenida/conductor.

## Presentación

- Bienvenida adaptable y desplazable, identidad Mexibús L2, ruta decorativa y
  autobús turquesa. Entrada de 240 ms, omitida con Reducir movimiento, sin bloquear
  los botones. Un toque abre el mapa.
- Splash nativo iOS en `LaunchScreen.storyboard`: nombre ZENTRYX mientras arranca
  Flutter. No hay temporizador de splash ni espera de la red.
- `HomeScreen` añade únicamente la barra Cupertino para volver. Cámara,
  seguimiento, selección, vehículo, mapa y modelos conservan su implementación.
- `LiveStatusIndicator` interpreta TransitState sin escribir en él. Usa la hora
  de telemetría disponible y, si falta, lastSuccess. Tras 30 s indica datos
  antiguos; un estado offline no se presenta como vivo durante un refresh.
- `SystemStatusBadge` y `SystemStatusCard` aceptan estados semánticos separados
  de los colores de marca. `TimeLabel` actualiza solo el texto y cancela su timer
  al salir, ocultarse o pasar a segundo plano.

## Conductor: límites de esta versión

`driverSessionProvider` es estado Riverpod en memoria: inicio, finalización,
último reporte y contador. Se conserva al cambiar de modo dentro de la app;
se pierde al cerrar el proceso. No hay autenticación, persistencia, GPS del
teléfono, permisos, peticiones HTTP ni envío de reportes/telemetría.

La Unidad 01 y la línea asignada son demostrativas. Los estados GPS/conexión
activos se etiquetan como simulados. La última actualización GPS muestra
"Sin telemetría real"; la hora del reporte local es real. El temporizador mide
desde startedAt y continúa correctamente al volver de otra pantalla/background.

## Preparado para el chip

Los componentes de estado reciben estado y timestamp, sin depender de un SDK GPS.
El mapa ya usa la API existente. La conexión futura del conductor deberá
reemplazar la sesión local con una fuente autorizada de GPS/conexión y un servicio
de reportes, con autenticación, permisos y confirmación real de envío. Esta versión
no cambia ningún contrato ni introduce un contrato alternativo.

## Validación

Ejecutar `flutter analyze` y `flutter test` en mobile. El workflow móvil existente
también genera Android debug e iOS Simulator. `app_navigation_test.dart` cubre
navegación, lifecycle sin red, recorrido/reportes, cancelación, estados y layouts
a 360/390/430 px, texto 1x/2x, claro/oscuro. Con
`--dart-define=ZENTRYX_CAPTURE_REVIEW=true` genera capturas reales de Flutter en
`build/visual-review`. Se mantienen las pruebas anteriores de mapa y movimiento.

La revisión en un iPhone físico sigue siendo necesaria para valorar haptics,
fluidez y la transición desde el splash del sistema.
