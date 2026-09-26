# Flujo de desarrollo

## Setup

```bash
git clone <repo>
cd zentryx
make setup
```

Selecciona `.venv/bin/python` como intérprete de PyCharm.

## Sesión normal

```text
Fetch/Pull → editar → make verify → commit → push
```

## App

```bash
make app
```

El launcher usa por defecto la API compartida y `unit-demo-01`.

## Tests

```bash
make verify
```

El backend de integración necesita `POSTGRES_URL`. En GitHub Actions se ejecuta contra PostGIS real. Localmente, sin esa variable, los tests de integración se omiten y los unitarios siguen corriendo.

## Cambios grandes

```bash
git switch -c feature/nombre
```

Abre PR a `main` cuando esté listo.

## Base de datos

- instalación nueva: `database/schema.sql`;
- instalación existente: nueva migración en `database/migrations/`;
- no reescribas migraciones que ya pudieron ejecutarse.

## Contratos

Si `contracts/` cambia, revisa backend, app, simulador y tests en el mismo cambio.
