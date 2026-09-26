# Zentryx Mobile

Cliente móvil nativo multiplataforma de Zentryx construido con Flutter.

Esta carpeta se desarrolla en paralelo con `app/` (Flet) hasta alcanzar paridad funcional. El backend, contratos HTTP, PostgreSQL/PostGIS, Docker y Tailscale no cambian.

## Objetivo

- iOS y Android con una sola base de código.
- Mapa, Línea 2, estaciones, unidad, ETA, heading y alertas consumiendo `/v1`.
- Diseño inspirado en Human Interface Guidelines usando identidad visual propia de Zentryx/Mexibús.
- Animaciones funcionales y suaves sin comprometer batería o estabilidad.

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
flutter pub get
flutter run --dart-define=ZENTRYX_API_BASE_URL=http://100.72.215.34:5000
```

Si todavía no existen `ios/` y `android/` en un checkout nuevo, ejecuta una vez:

```bash
flutter create . --platforms=ios,android --org com.zentryx --project-name zentryx_mobile
```

El comando genera solo el scaffold nativo estándar. Conserva los archivos de `lib/` de este repositorio.

## Estructura

```text
lib/
  app/            configuración global
  core/           red y configuración
  design_system/  tokens y componentes visuales
  features/       dominio, datos, estado y pantallas
```

El contrato funcional continúa siendo `../contracts/api_v1.md`.

## Estado de migración

La app Flet continúa siendo el cliente estable. `mobile/` es la nueva implementación y no reemplazará `app/` hasta alcanzar paridad funcional y pasar pruebas en iOS y Android.
