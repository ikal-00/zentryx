# Desarrollo local y compartido

## Entorno e IDE

Clona `ikal-00/zentryx` con GitHub Desktop. Abre la raíz en PyCharm, crea `.venv` con Python 3.12+ e instala `python -m pip install -r requirements-dev.txt`.

macOS/Linux: `source .venv/bin/activate`. PowerShell: `.venv\Scripts\Activate.ps1`. Usa ese intérprete y la raíz como directorio de trabajo en PyCharm.

## App

Demo local: `python -m flet run --web app/main.py`, sin `ZENTRYX_API_BASE_URL`.

Compartida: conecta Tailscale y ejecuta `make app` en macOS/Linux. El launcher reconoce `app/.venv` antiguo y `.venv` de raíz. Para PyCharm/Windows configura:

```text
ZENTRYX_API_BASE_URL=http://100.72.215.34:5000
ZENTRYX_SERVICE_ID=l2-ordinary
ZENTRYX_VEHICLE_ID=unit-demo-01
```

Ejecuta `app/main.py`. En ejecución directa, modo API conserva `unit-01` por compatibilidad: selecciona `unit-demo-01` explícitamente para la demo compartida.

## Servidor local

Copia `.env.example` a `.env`, configura contraseña y `API_BIND_IP=127.0.0.1`. Ejecuta `docker compose --profile demo up -d --build`. Usa las variables de app anteriores con URL `http://127.0.0.1:5000`.

La app recibe variables por shell/PyCharm, no carga `.env` automáticamente. Compose carga `.env` de raíz. Flask sin Docker carga el mismo archivo y necesita `POSTGRES_URL` hacia una base accesible; el Compose normal no publica PostgreSQL al host.

## Pruebas desde raíz

```bash
python -m ruff check app backend scripts
python -m compileall -q app backend scripts
python -m unittest discover -s app/tests -v
python -m unittest discover -s backend/tests -v
```

`make verify` agrupa los checks. Frontend prueba interacciones y adapters; backend, contrato, navegación y servicios. Sin `TEST_DATABASE_URL` se omite `test_postgres_integration.py`.

Integración necesita una base PostGIS desechable cuyo nombre termine en `_test`. **La suite vacía sus tablas; nunca uses la compartida.** El nombre se comprueba antes de conectar. CI crea `zentryx_test` aislada y verifica simulador → HTTP → DB → adapters reales.

`scripts/check_container.sh` solo se ejecuta en el proyecto desechable `zentryx-ci` de Actions. Construye imágenes y comprueba persistencia.

Smoke de solo lectura: `python scripts/check_shared_api.py`. Acepta URL y unidad como argumentos; necesita demo activa para verificar posición, ETA y alertas. Una terminal sin próxima estación es válida si distancia y ETA son cero.

## Colaboración

Fetch/Pull → rama → desarrollar → test → commit → push → PR → merge → auto-deploy. Ver [CONTRIBUTING](../../CONTRIBUTING.md).
