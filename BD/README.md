# Zentryx · Base de datos

La fuente de verdad actual es `database_v1.sql`.

## Base nueva

```bash
psql "$POSTGRES_URL" -f BD/database_v1.sql
```

El archivo ya incluye PostGIS, rutas/servicios, estaciones, dispositivos, unidades, telemetría, alertas, incidentes y la vista `vehicle_latest_telemetry`.

## Base existente

Si la base fue creada antes de la alineación de API, ejecuta:

```bash
psql "$POSTGRES_URL" -f BD/migrations/002_api_alignment.sql
```

La migración agrega metadatos de línea/servicio a `routes` y documenta el formato de `devices.token_hash`.

## Archivo legado

`Gps_sql/Gps_sql.sql` está deprecado. No debe ejecutarse: usaba nombres de tablas incompatibles con la API actual y se conserva solo como referencia histórica.

## Tokens

`devices.token_hash` no guarda el token en texto plano. Formato canónico:

```text
sha256:<64 caracteres hexadecimales>
```

Generación rápida:

```bash
python -c "import hashlib; t='TU_TOKEN'; print('sha256:'+hashlib.sha256(t.encode()).hexdigest())"
```
