# Prototipos de Zentryx

Trabajo experimental que no forma parte del runtime desplegado.

- `station-3d/`: representación 3D de estación e infraestructura.
- `game/`: simulador/juego para validar la experiencia de usuario.
- `firmware/`: espacio reservado para el futuro código del dispositivo físico de telemetría/GPS.

El diseño electrónico activo vive en `hardware/`; los prototipos pueden evolucionar con su propio stack sin contaminar dependencias de `app/` o `backend/`.
