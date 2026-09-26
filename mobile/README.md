# Zentryx Mobile

Cliente móvil nativo multiplataforma de Zentryx construido con Flutter.

Esta carpeta se desarrolla en paralelo con `app/` (Flet) hasta alcanzar paridad funcional. El backend, contratos HTTP, PostgreSQL/PostGIS, Docker y Tailscale no cambian.

## Objetivo

- iOS y Android con una sola base de código.
- Mapa, Línea 2, estaciones, unidad, ETA, heading, ocupación y alertas consumiendo `/v1`.
- Diseño inspirado en Human Interface Guidelines usando identidad visual propia de Zentryx/Mexibús.
- Animaciones funcionales y suaves sin comprometer batería o estabilidad.
- Mantener la app utilizable cuando la API se desconecta mostrando el último estado válido.

## Backend compartido

Por defecto se usa:

```text
http://100.72.215.34:5000
```

Esa dirección solo es alcanzable cuando Tailscale está conectado.

## Ejecutar

Con Flutter 3.24+ instalado:

```bash
cd mobile
./bootstrap.sh
flutter run --dart-define=ZENTRYX_API_BASE_URL=http://100.72.215.34:5000
```

`bootstrap.sh` genera una vez el scaffold estándar iOS/Android si hace falta, instala dependencias, ejecuta el analyzer y corre los tests.

También puede hacerse manualmente:

```bash
flutter create . --platforms=ios,android --org com.zentryx --project-name zentryx_mobile
rm -f test/widget_test.dart
flutter pub get
flutter run
```

Los archivos de `lib/` son la implementación de Zentryx y deben conservarse.

## Estructura

```text
lib/
  app/            configuración global y lifecycle
  core/           red y configuración
  design_system/  tokens, tema y marca visual
  features/
    transit/
      application/ estado y polling
      data/        acceso a la API y caché
      domain/      modelos del contrato v1
      presentation/ mapa, HUD y animaciones
```

El contrato funcional continúa siendo `../contracts/api_v1.md`.

## Rendimiento

- Ruta y estaciones se cachean en memoria porque son datos estáticos durante una sesión.
- La posición del vehículo se consulta cada 2 s y se interpola visualmente entre muestras.
- El heading usa la rotación más corta para evitar giros visuales de 360°.
- El polling se pausa cuando la app entra en segundo plano y se refresca al volver.
- Los componentes con blur/animación están aislados con `RepaintBoundary` cuando aporta valor.

## CI móvil

`.github/workflows/mobile-flutter.yml` valida la rama móvil en GitHub Actions:

- `flutter analyze`
- `flutter test`
- APK Android debug
- build iOS para simulador

Los builds exitosos publican artefactos temporales `zentryx-android-debug` y `zentryx-ios-simulator` durante 7 días.

## Estado de migración

La app Flet continúa siendo el cliente estable. `mobile/` es la nueva implementación y no reemplazará `app/` hasta alcanzar paridad funcional y pasar pruebas reales en iOS y Android.
