# Operación y despliegue

## Contrato operativo

- Checkout: `/home/miner3/zentryx`.
- Runner `zentryx-server`: `self-hosted`, `linux`, `x64`, `zentryx`.
- API privada Tailscale: `http://100.72.215.34:5000`.
- Compose en raíz, proyecto `zentryx`; `db`, `api`, `simulator` (perfil `demo`).
- Volumen lógico `zentryx_db`; nombre Docker predeterminado `zentryx_zentryx_db`.
- `.env` permanece en el servidor y no se imprime ni versiona.

## CI/CD

`ci.yml` responde a push y PR: app/lint, backend/PostGIS y Docker/persistencia. Solo un push a `main` con todos correctos invoca `deploy.yml` reutilizable. No se ejecuta código de PR en el runner compartido.

CD obtiene `scripts/deploy.sh` del commit validado, comprueba que siga en la cabeza de `main`, actualiza el checkout a ese SHA y ejecuta `docker compose --profile demo up -d --build --remove-orphans`. Si `main` avanzó, falla explícitamente; el nuevo push tiene su propia ejecución. La concurrencia evita despliegues simultáneos y no cancela uno a mitad.

El smoke verifica health, readiness, ruta, 43 estaciones, unidad online, posición, dirección, ETA y alertas. Los reintentos permiten recibir la primera muestra del simulador.

## Persistencia

No cambies nombre de proyecto, clave de volumen o ruta de datos al reorganizar. Nunca elimines volúmenes persistentes. `make server-stop` detiene servicios sin borrar datos.

El esquema montado en `/docker-entrypoint-initdb.d/` solo inicializa volúmenes vacíos. Reconstruir API no aplica migraciones. Esta refactorización no cambia esquema ni migraciones. Cambios futuros requieren respaldo y aplicación coordinada; no hay rollback automático de datos.

El seed actualiza ruta L2, estaciones y orden. El simulador aprovisiona IDs demo, genera token nuevo al arrancar y continúa la secuencia persistida. Es una herramienta de desarrollo, no un sustituto del GPS real.

## Diagnóstico

```bash
cd /home/miner3/zentryx
docker compose --profile demo ps
docker compose --profile demo logs --tail=150 api simulator
python3 scripts/check_shared_api.py
```

Si CI falla, no hay deploy. Si CD falla, revisa su paso y estado de servicios; no asumas rollback. Para regresar código, crea un revert por PR y deja que CI/CD lo despliegue. Nunca borres datos para reparar la app.

Reconstrucción manual del checkout revisado: `docker compose --profile demo up -d --build`.

## Persistencia en CI

El proyecto `zentryx-ci` corre en un runner hospedado. Arranca la imagen real, registra una fila, detiene servicios, recrea DB y verifica que la fila y flujo demo sobrevivan. No utiliza el servidor compartido ni sus volúmenes.
