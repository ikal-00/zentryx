# Navegación, recorrido y dispositivo

## Flujo

Un único Navigator Cupertino conserva `/` (bienvenida), `/passenger` (mapa) y
`/driver`. DriverScreen restaura la sesión local. Si no hay recorrido, muestra
PrepareTripScreen: unidad, línea, dispositivo, fuente, comprobaciones e inicio.
Al iniciar, el mismo destino muestra el dashboard activo; al finalizar vuelve a
preparación. Diagnóstico de unidad se abre con una CupertinoPageRoute desde ambas
pantallas y vuelve sin reiniciar la sesión. La bienvenida no espera a la API.

No se modifica HomeScreen, TransitState, polling, movimiento, seguimiento, API,
backend ni contratos existentes. El simulador del conductor es independiente del
vehículo del mapa. No se añaden controles de debug en producción.

## Fuente intercambiable

`DeviceTelemetrySource` expone `initial`, `updates`, `start`, `pause` y `dispose`.
El adaptador publica snapshots inmutables `DeviceTelemetry`; el controlador
Riverpod se suscribe antes de iniciar, transforma errores/cierre del stream en
estados explícitos y libera la suscripción. Los providers autoDispose liberan la
fuente cuando se abandona el modo conductor. El lifecycle pausa la fuente en
segundo plano y la reanuda al volver. No es un servicio GPS en background.

El punto de composición es `deviceTelemetrySourceProvider`. Para integrar el
hardware, implementar `HardwareDeviceTelemetrySource` y cambiar únicamente esa
factoría (o sobreescribir el provider). Las pantallas consumen el mismo estado y
no importan el simulador. No se define aún BLE, USB, Wi-Fi, HTTP ni un protocolo
físico; eso depende del dispositivo que finalmente se elija.

### Datos internos esperados

| Campo | Significado |
|---|---|
| deviceId, firmware | Identidad del dispositivo y versión opcional |
| unit.id / name / line | Identificador estable de unidad y textos de presentación |
| sourceType / sourceLabel | Origen declarado; `simulated` muestra Entorno de simulación |
| connected / signal | Estado del enlace; esperando, sincronizando, listo, desconectado o fallo |
| gpsAvailable | Disponibilidad del fix, independiente del enlace al servidor |
| serverConnected | Disponibilidad declarada por el adaptador; no implica envío de reportes |
| latitude / longitude | Grados decimales WGS84, opcionales, finitos y dentro de rango |
| accuracyMeters | Precisión opcional, finita y no negativa |
| lastPacketAt | Instante UTC de recepción del último paquete real del adaptador |
| lastGpsFixAt | Instante UTC del último fix válido, distinto de la recepción del paquete |

El adaptador debe normalizar/reconciliar el reloj del chip; no reemplazar un fix
viejo con la hora de recepción. El criterio interno de frescura es 10 s y rechaza
relojes adelantados más de 2 s. Es configurable en el modelo cuando se conozca la
cadencia del hardware, no un nuevo contrato HTTP. La UI envejece los datos aunque
no lleguen paquetes: nunca deja verde un enlace con telemetría atrasada. Un fix
antiguo puede conservar coordenadas en diagnóstico, etiquetadas como últimas
conocidas. Una fuente de otra unidad no se presenta como la unidad del recorrido.

## Simulación

`SimulatedDeviceTelemetrySource` emite cada 2 s, con ZTX-GPS-001, Unidad 01,
Mexibús Línea 2, firmware SIM 1.0, coordenadas fijas de demostración y precisión
variable entre 4 y 6 m. No mueve el autobús del mapa. Publica timestamps UTC del
reloj inyectable. No hace HTTP ni usa sensores, ubicación del teléfono o permisos.

El constructor permite escenarios internos: operativo, desconectado, sin GPS,
sin servidor, atrasado, esperando paquete, sincronizando y fallo. Los tests
inyectan la fuente/escenario; no hay selector de fallos visible para el conductor.

Se reutilizan SystemStatusBadge, SystemStatusCard y TimeLabel, extendiendo el
enum semántico con advertencia y sin datos. DeviceChecks compone esos componentes.
El rojo de marca sigue separado del rojo de error; nada depende solo del color.

## Persistencia

`DriverSessionStore` tiene solo read/write de un documento versionado.
`PreferencesDriverSessionStore` usa SharedPreferencesAsync bajo la clave propia
`zentryx.driver.session.v1`, sin base de datos ni caché de preferencias en Dart.
Se guarda únicamente startedAt UTC, unidad seleccionada, último incidente y su
hora, y contador de reportes. No se almacenan coordenadas, credenciales ni datos
personales. No se persiste la telemetría; se adquiere otra vez al abrir.

El controlador espera la restauración antes de aceptar cambios y serializa las
escrituras. La UI confirma después de que el almacenamiento acepte el cambio.
Si una escritura falla conserva el estado anterior y muestra un error; se puede
repetir la acción. Si la lectura o el documento son inválidos no sobreescribe la
sesión desconocida: ofrece reintentar. Un documento corrupto que siga fallando
requiere recuperar o borrar esa clave local durante mantenimiento; no se elimina
silenciosamente. No se borran otras preferencias.

El temporizador se reconstruye desde startedAt: no hay escrituras por segundo.
Volver al inicio, cerrar y volver a abrir conserva el recorrido. Finalizar guarda
startedAt nulo, preservando unidad y último incidente. Las preferencias son
persistencia básica, no almacenamiento transaccional crítico; una terminación
brusca durante una escritura o un fallo del sistema puede perder el último cambio.
Referencia del plugin: https://pub.dev/packages/shared_preferences

Los cinco incidentes siguen siendo locales. La confirmación dice Registrado
localmente y el dashboard muestra tipo/hora. No hay envío, reintento de red,
autenticación ni autorización de conductor implementados.

## Pendiente con hardware/backend

Definir transporte, asociación chip-unidad, normalización de timestamps,
reconexión y permisos requeridos; implementar el adaptador y probar el hardware.
Para subir telemetría/reportes reales hace falta autenticación, autorización,
confirmación del servidor y una estrategia de cola/envío, usando los contratos
existentes o cambios acordados por separado. El snapshot interno no los sustituye.

## Validación

`flutter analyze` y `flutter test`; CI también construye Android debug e iOS
Simulator. Las 39 pruebas originales se conservan/adaptan al guardado asíncrono.
Se añaden escenarios de fuente, errores/cierre de stream, pausa/resume, inicio y
restauración en otro controlador/ProviderScope, finalización persistida, reportes,
errores de lectura/escritura y orden de escrituras. Preparación y diagnóstico se
comprueban a 360/390/430 px, texto 1x/2x, claro/oscuro. Las capturas opcionales se
generan con `--dart-define=ZENTRYX_CAPTURE_REVIEW=true` en build/visual-review.
Las pruebas de persistencia inyectan almacenamiento controlado. El cierre forzado
y recuperación con el plugin nativo, los haptics y la fluidez se deben verificar
además en un iPhone/Android físico; no se afirma esa validación aquí.
