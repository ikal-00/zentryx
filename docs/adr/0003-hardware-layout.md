# ADR 0003: separar hardware físico y firmware

- Estado: Aceptada
- Fecha: 2026-09-25
- Amplía ADR 0001.

## Contexto

El proyecto KiCad Silice entró al repositorio en paralelo al refactor dentro de `firmware/Silice/`. Ese nombre mezclaba dos conceptos distintos: diseño electrónico (PCB/esquemático) y firmware ejecutable del dispositivo.

## Decisión

Usar `hardware/` para diseño electrónico y archivos KiCad. El proyecto activo queda en `hardware/silice/`.

Reservar `prototypes/firmware/` para el futuro código ejecutable del dispositivo de telemetría/GPS. Hasta su integración, `backend/dev_simulator.py` sigue produciendo telemetría de desarrollo.

Excluir de Git los artefactos temporales de KiCad (locks, cachés y backups). Los modelos, símbolos, footprints, esquemático y PCB que sí forman parte del diseño permanecen versionados.

## Consecuencias

- la raíz distingue software, hardware y prototipos con nombres no ambiguos;
- mover el checkout puede requerir que colaboradores actualicen referencias locales, pero las librerías KiCad usan `${KIPRJMOD}` y conservan rutas relativas;
- ERC/DRC y validación eléctrica continúan fuera del CI de Python.
