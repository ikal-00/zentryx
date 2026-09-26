# Contribuir

`main` representa la versión estable y desplegable. Usamos ramas cortas y PR, sin GitFlow.

1. GitHub Desktop: **Fetch origin → Pull origin** sobre `main`.
2. **Branch → New branch**: `feature/*`, `fix/*`, `refactor/*` o `docs/*`.
3. Abre la raíz en PyCharm y selecciona `.venv/bin/python` (Windows: `.venv/Scripts/python.exe`).
4. Implementa y ejecuta `make verify`; alternativas Windows en la [guía](docs/development/workflow.md).
5. Revisa el diff, commit descriptivo y **Push origin → Create Pull Request**.
6. Revisa con tu compañero y fusiona solo cuando CI esté correcto.
7. El merge actualiza `main`, ejecuta CI y dispara CD.

No experimentes directamente en `main`. Coordina ediciones del mismo archivo.

## Reglas

- Cambios contractuales actualizan consumidores, servidor y pruebas en el mismo PR.
- Separa lógica pura de Flet/Flask/SQL; evita capas sin responsabilidad.
- Bases nuevas usan `database/schema.sql`; bases existentes, migraciones nuevas. No reescribas migraciones aplicadas.
- Integración solo usa `TEST_DATABASE_URL`, base desechable terminada en `_test`; vacía sus tablas.
- Nunca subas `.env`, tokens, claves privadas, dumps reales o credenciales.
- Deployment conserva proyecto/volumen Compose y `/home/miner3/zentryx`.

Consulta [arquitectura](docs/architecture/overview.md) y [operación](docs/operations/deployment.md).
