# Zentryx

Plataforma de movilidad para Mexibús Línea 2: mapa, ubicación de unidades, próxima estación, ETA y alertas. Monorepo modular para dos desarrolladores.

## Componentes

| Directorio | Responsabilidad |
| --- | --- |
| `app/` | Python/Flet: pantalla, componentes, estado y adaptadores REST |
| `backend/` | Flask/Gunicorn: HTTP, servicios, SQL y simulador optativo |
| `database/` | PostgreSQL/PostGIS: esquema y migraciones |
| `contracts/` | Endpoints y mensajes de API v1 |
| `docs/` | Arquitectura, desarrollo, decisiones y operación |
| `scripts/` | Smoke test, validación de contenedores y despliegue |
| `hardware/` | Diseño electrónico/KiCad del dispositivo Silice |
| `prototypes/` | Firmware experimental, juego y estación 3D |
| `.github/workflows/` | CI hospedado y CD en la mini PC |

La app consulta `/v1`. El simulador envía telemetría a esa misma API. PostgreSQL/PostGIS conserva datos; el backend calcula navegación y ETA. Docker Compose ejecuta el servidor y Tailscale permite acceso privado.

## Empezar

Python 3.12+ para desarrollo; CI e imagen de servidor usan 3.13.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m flet run --web app/main.py
```

El último comando inicia la demo local. Con Tailscale conectado, `make app` usa la API compartida y `make smoke` la comprueba.

Para servidor local, copia `.env.example` a `.env`, configura contraseña y `API_BIND_IP=127.0.0.1`, y ejecuta `make server-up`. Nunca añadas `.env` a Git.

## Desarrollo y entrega

```bash
make verify        # lint, compilación y pruebas
make server-status # servicios Docker
make server-stop   # detener sin eliminar datos
```

La integración requiere `TEST_DATABASE_URL` hacia una base desechable cuyo nombre termine en `_test`. Nunca usa `POSTGRES_URL` como destino implícito. CI prueba PostGIS, flujo HTTP hasta los adaptadores Flet y persistencia Docker.

Fetch/Pull → rama → desarrollar → test → commit/push → PR → merge → CI → CD.

Un push a `main` despliega después de aprobar app, backend y contenedores. Se conserva `/home/miner3/zentryx`, el runner `zentryx-server` y el volumen existente.

- [Desarrollo y PyCharm](docs/development/workflow.md)
- [Arquitectura](docs/architecture/overview.md)
- [Docker y despliegue](docs/operations/deployment.md)
- [Contribuir](CONTRIBUTING.md) · [Seguridad](SECURITY.md)
- [API v1](contracts/api_v1.md) · [Base de datos](database/README.md)
