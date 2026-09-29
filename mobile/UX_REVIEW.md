# Movimiento y experiencia móvil — revisión 2026-09-28

## Fuente y baseline

Código de partida: `main` en `9d2ebafb329124a2e0221f4933f7355561723a15`.
ZIP de referencia: `zentryx-ios-simulator (1)(2).zip`, aplicación
`com.zentryx.zentryxMobile`, versión 0.1.0 (1), iOS Simulator, mínimo iOS 15.
Solo se inspeccionaron listado y metadatos del ZIP; no se modificó ni se usó
su contenido compilado como fuente. El entorno Linux no ejecuta iOS Simulator:
no hay una comparación visual medida contra esa build ni una medición de FPS.

## Arquitectura y diferencias encontradas antes del cambio

`mobile/` es el cliente destinado a iOS/Android; `app/` sigue de respaldo.
Flutter consume los mismos servicios `/v1`; no depende del proceso Flet.
Flet ofrece además simulación local y cálculo local de navegación para su modo
sin API. Flutter usa el simulador del backend: no se duplica esa lógica.
Flet ya tenía un panel de estación no modal y un detalle de alerta; Flutter
mostraba una estación en un action sheet, alertas truncadas y un contador de
alertas adicionales sin acceso al contenido completo. Flutter ya ofrecía
progreso, velocidad, caché de datos estáticos y polling pausado por lifecycle.
Se conservan esos datos, con velocidad/progreso/distancia/hora en Detalles.

## Causas localizadas

- `AnimatedVehicleLayer` interpolaba por 1900 ms con `easeOutCubic`, frenando
  en cada muestra de un polling de 2 s. No faltaban puntos de ruta.
- `HomeScreen` centraba de golpe la cámara en la posición real de cada respuesta,
  adelantándose a la posición que todavía estaba animando el marcador.
- Recentrar o seleccionar estaciones también movía y cambiaba zoom de golpe.
- Las estaciones eran círculos de 14 px sin estado activo/próxima parada.
- La ruta dependía de un color dinámico que se volvía claro sobre tiles claros.

## Solución

- `VehicleMotion`: posición/heading visuales separados del modelo recibido.
  Retarget desde el punto que se estaba dibujando; avance lineal con duración
  adaptada a la cadencia recibida (0.8–3 s) y distancia (hasta 5 s para recuperación).
  Rotación por arco corto; bearing de trayectoria cuando falta heading.
- Coordenadas inválidas y timestamps repetidos/anteriores se descartan. Jitter
  menor de 1.5 m se retiene. Un salto incompatible con 55 m/s y margen de precisión
  requiere dos fixes distintos y cercanos entre sí para recuperar suavemente.
  Estos límites son heurísticas visuales, no validación de telemetría del backend.
- La cámara recibe el punto visual, converge progresivamente sin cambiar zoom y
  usa una zona muerta de aproximadamente 2 px. Sus ticks se detienen al alcanzar
  el objetivo. Un gesto cancela inmediatamente el seguimiento y el centrado.
- El marcador es un autobús vectorial original con `CustomPainter`, aislado por
  `RepaintBoundary`. No se copian assets ni se recalcula la ruta por frame.
- Ruta: halo blanco, cuerpo verde oscuro y centro lima. Estaciones de 19/30 px,
  halo y selección contrastantes, con áreas táctiles de 48 px. Vehículo encima.
- Panel no modal de estación, reemplazable con otro toque. Solo se presenta ETA
  para la próxima estación que identifica el backend; no se inventan llegadas
  ni estado operativo para las demás. Alertas son del servicio, no atribuidas
  sin evidencia a una estación particular.
- HUD: línea, unidad, siguiente estación, ETA, dirección, ocupación y estado.
  Datos secundarios y todas las alertas accesibles en detalle. ETA se oculta al
  quedar offline/stale. SafeArea y panel con altura máxima/scroll para alturas
  pequeñas o texto ampliado. Atribución OSM visible fuera del panel.

## Validación y límites

Tests Python: `python -m unittest discover -s app/tests -v` y equivalente backend.
Tests nuevos Flutter: interpolación, retarget, heading/norte, outliers, fixes
antiguos, jitter, cámara, identidad de estación, selección/cambio/cierre,
exploración/seguir, alertas completas, ETA stale y anchos 360/390/430 con texto
1.0x y 1.6x. CI conserva analyzer, tests, APK y build de iOS Simulator.

CI también puede producir capturas del widget real con tiles sólidos de prueba
(sin red) mediante `--dart-define=ZENTRYX_CAPTURE_REVIEW=true`. Sirven para
revisar distribución y overlays, no para afirmar contraste con OSM real.

Pendiente de validación en dispositivo: fluidez percibida y FPS sostenidos,
trazado real en curvas (interpolación recta entre fixes; no map matching),
contraste con tiles reales, interrupción GPS prolongada y recuperación,
notch/Dynamic Island y gestos nativos. La build anterior no incorpora una
referencia verificable a un commit; no se presume identidad exacta con main.
