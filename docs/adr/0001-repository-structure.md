# ADR 0001: estructura del monorepo

- Estado: Aceptada
- Fecha: 2026-09-25

## Contexto

Zentryx combina app, API, datos geoespaciales, base de datos, prototipos y despliegue. La estructura inicial creció de forma incremental y mezclaba nombres, archivos legacy y carpetas vacías en la raíz.

## Decisión

Mantener un monorepo con dominios de primer nivel estables: `app/`, `backend/`, `database/`, `contracts/`, `docs/`, `prototypes/` y `scripts/`.

`backend/routes/` concentra los blueprints HTTP. `backend/app.py` es el entrypoint canónico de Flask. `backend/API_Global.py` se conserva temporalmente como wrapper de compatibilidad.

Cada componente conserva su `requirements.txt` de producción y `requirements-dev.txt` en raíz los combina para desarrollo.

CI y deploy se consolidan en un único workflow para impedir despliegues de commits que no hayan pasado pruebas.

## Consecuencias

### Positivas

- navegación más predecible;
- menos fuentes de verdad duplicadas;
- separación explícita entre producto y prototipos;
- onboarding más rápido;
- CI/CD más fácil de razonar.

### Costes

- paths históricos cambian (`BD/` → `database/`);
- integraciones externas con paths antiguos deben actualizarse;
- `API_Global.py` deberá retirarse en una futura limpieza cuando no exista dependencia externa.
