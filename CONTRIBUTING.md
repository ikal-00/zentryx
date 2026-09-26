# Contribuir a Zentryx

El objetivo es conservar un flujo simple para un equipo pequeño sin perder disciplina de ingeniería.

## Antes de trabajar

Actualiza tu copia local:

```bash
git pull --ff-only
```

En GitHub Desktop: **Fetch origin** y luego **Pull origin** si aparece.

## Entorno

```bash
make setup
```

PyCharm debe usar `.venv/bin/python`.

## Ramas

`main` representa la versión desplegable.

Para cambios pequeños coordinados puede usarse `main` directamente. Para cambios grandes, refactors o trabajo paralelo usa:

```text
feature/<nombre>
fix/<nombre>
chore/<nombre>
```

## Antes de hacer push

```bash
make verify
```

No hagas commit de secretos, `.env`, claves SSH, archivos generados por el IDE o bases locales.

## Commits

Usa mensajes breves y descriptivos, por ejemplo:

```text
Add driver incident form
Fix shared API reconnect
Refactor vehicle navigation service
```

## Contratos

Los cambios en `contracts/` son cambios de interfaz. Si modificas un contrato, actualiza backend, consumidores, tests y documentación en el mismo cambio.

## Base de datos

`database/schema.sql` es la fuente de verdad para una instalación nueva.

Los cambios para bases existentes deben agregarse como migraciones numeradas en `database/migrations/`. No reescribas migraciones que ya pudieron aplicarse en el servidor compartido.

## Deploy

Un push a `main` ejecuta CI y, si pasa, el runner self-hosted actualiza la mini PC automáticamente.
