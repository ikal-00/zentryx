# ADR 0002: límites internos y entrega validada

- Estado: Aceptada
- Fecha: 2026-09-25
- Complementa ADR 0001; sustituye la decisión de concentrar CI/CD en un solo archivo.

## Decisión

Conservar directorios principales, factory Flask, Compose y ubicación de datos. Extraer SQL a repositorios y reglas a servicios. Las lecturas simples no necesitan servicios vacíos. Validación y hashing son módulos puros.

Separar en Flet entrypoint, pantalla, modelos, configuración, estado y composición de fuentes. Mantener geometrías donde el empaquetado las espera.

CI invoca CD reutilizable mediante `needs`: separar archivos no pierde el gate. CD despliega el SHA validado. Tests DB tienen variable propia y rechazan bases sin sufijo `_test`.

## Costes

Más módulos pequeños con responsabilidades explícitas. Persisten wrappers legacy y duplicación matemática deliberada. No se modifica contrato HTTP ni esquema, ni se introduce ORM, DI, microservicios o nueva tecnología.
