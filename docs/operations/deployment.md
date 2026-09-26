# Operación y despliegue

## Servidor compartido

La mini PC ejecuta PostgreSQL/PostGIS, API Flask/Gunicorn, simulador demo y el GitHub Actions self-hosted runner.

La API se enlaza a la IP Tailscale configurada en `.env`. PostgreSQL permanece interno a Docker.

## Auto-deploy

Cada push a `main` inicia `Zentryx CI`. Primero se ejecutan los checks de app y backend en runners hospedados por GitHub. Solo si ambos terminan correctamente comienza `Deploy to mini PC`.

El runner:

1. actualiza `/home/miner3/zentryx` a `origin/main`;
2. reconstruye los contenedores;
3. levanta el perfil `demo`;
4. muestra estado;
5. ejecuta `scripts/check_shared_api.py`.

## Diagnóstico manual

```bash
ssh miner3@100.72.215.34
cd ~/zentryx
docker compose --profile demo ps
docker compose --profile demo logs -f --tail=150
```

Reconstrucción manual:

```bash
git fetch origin main
git reset --hard origin/main
docker compose --profile demo up -d --build --remove-orphans
```

## Persistencia

La base vive en `zentryx_db`. No uses `docker compose down -v` salvo que quieras borrar deliberadamente la base de desarrollo.

## Verificación

```bash
python3 scripts/check_shared_api.py http://100.72.215.34:5000
```
