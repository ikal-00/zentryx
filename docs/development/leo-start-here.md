# Leo: empieza aquí

Esta guía es para ubicarte rápido después de la reorganización de Zentryx.

## 1. Qué hace cada carpeta importante

| Ruta | Para qué sirve |
| --- | --- |
| `app/` | Interfaz Flet para pasajeros. Mapa, pantallas, estado y conexión con la API. |
| `backend/` | API Flask, lógica de negocio, telemetría, navegación, ETA, incidentes y simulador. |
| `backend/routes/` | Endpoints HTTP. Aquí entra una petición a la API. |
| `backend/services/` | Lógica de negocio. Coordina datos y reglas. |
| `backend/repositories/` | Acceso a PostgreSQL/PostGIS y SQL. |
| `database/` | Esquema, migraciones y archivos legacy de la base de datos. |
| `contracts/` | Contrato de la API v1: requests, responses y formatos compartidos. |
| `scripts/` | Smoke tests, validaciones y scripts de despliegue. |
| `docs/` | Arquitectura, desarrollo y operación del proyecto. |
| `hardware/` | Diseño electrónico físico. KiCad, PCB, esquemático, símbolos y footprints. |
| `prototypes/` | Trabajo experimental que todavía no forma parte del producto principal. |

## 2. Dónde está tu trabajo actual

Tu proyecto de KiCad **Silice** ahora está en:

```text
hardware/silice/
```

El archivo principal para abrir el proyecto es:

```text
hardware/silice/Silice.kicad_pro
```

Antes estaba en `firmware/Silice/`, pero se movió porque KiCad es **hardware**, no firmware.

Dentro de `hardware/silice/` encontrarás:

```text
Silice.kicad_pro   -> proyecto KiCad
Silice.kicad_sch   -> esquemático
Silice.kicad_pcb   -> PCB
Components/        -> símbolos, footprints y modelos 3D usados por el proyecto
fp-lib-table       -> librerías de footprints
sym-lib-table      -> librerías de símbolos
```

**Continúa trabajando ahí.** No necesitas tocar `app/`, `backend/` ni `database/` para seguir con la PCB.

## 3. ¿Y `prototypes/firmware/`?

`prototypes/firmware/` queda reservado para el código que en el futuro corra dentro del dispositivo físico, por ejemplo ESP32/microcontrolador, lectura GPS y envío de telemetría.

Por ahora el GPS real todavía se sustituye con:

```text
backend/dev_simulator.py
```

Así que:

- diseño electrónico / PCB -> `hardware/silice/`
- futuro código del dispositivo -> `prototypes/firmware/`
- simulación actual de GPS/telemetría -> `backend/dev_simulator.py`

## 4. Flujo normal para trabajar

Antes de empezar:

```text
GitHub Desktop
-> main
-> Fetch origin
-> Pull origin
```

Después crea una rama para tu cambio, por ejemplo:

```text
hardware/silice-usb
hardware/silice-power
fix/silice-pcb
```

Trabaja, guarda en KiCad, revisa los cambios, haz commit, push y PR.

No trabajes directamente sobre `main` si el cambio todavía está en progreso.

## 5. Archivos que NO debes subir de KiCad

Git ya está configurado para ignorar archivos temporales como locks, cachés y backups.

No fuerces al repositorio archivos como:

```text
~*.lck
fp-info-cache
*-backups/
*.kicad_prl
autosave-*
```

Los archivos reales de diseño (`.kicad_pro`, `.kicad_sch`, `.kicad_pcb`, símbolos, footprints y modelos necesarios) sí deben versionarse.

## 6. Cómo se conecta tu parte con Zentryx

Tu hardware terminará produciendo la ubicación real de una unidad.

El flujo esperado es:

```text
GPS / dispositivo Silice
        ↓
firmware del dispositivo
        ↓
POST /v1/telemetry
        ↓
backend/
        ↓
PostgreSQL/PostGIS
        ↓
app/
```

La API ya tiene el endpoint de telemetría y actualmente el simulador hace el papel del dispositivo físico. Cuando el prototipo esté listo, la idea es reemplazar el simulador por tu hardware sin cambiar el resto de la arquitectura.

## 7. Si solo quieres continuar donde te quedaste

Haz Pull de `main`, abre:

```text
hardware/silice/Silice.kicad_pro
```

y continúa el diseño de Silice desde ahí.

Si tienes cambios locales viejos dentro de `firmware/Silice/` que todavía no subiste, **no los borres**: guárdalos/commitéalos primero y luego mueve esos cambios al nuevo `hardware/silice/`.
