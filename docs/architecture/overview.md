# Arquitectura

## Flujo real

Flet carga ruta/estaciones y consulta unidad/alertas periódicamente. Sin API configurada usa demo local. Si falla la carga inicial de ruta puede usar GeoJSON; una desconexión conserva la última posición y oculta ETA.

El simulador compartido aprovisiona dispositivo, unidad y alerta demo en PostgreSQL. Luego publica `/v1/telemetry` con token efímero. La API valida, autentica y guarda idempotentemente. La lectura de vehículos combina última muestra, historial reciente, proyección sobre ruta y próxima estación. En modo API, el servidor es autoridad de navegación y ETA.

## Backend

| Módulo | Responsabilidad |
| --- | --- |
| `app.py` | Factory Flask, blueprints y traducción de errores |
| `config.py` | Entorno del pool y ubicación estable de assets |
| `routes/` | HTTP, parámetros y respuestas |
| `services/` | Autenticación de asignaciones, telemetría, incidentes, navegación y movimiento demo |
| `repositories/` | SQL parametrizado y transacciones, sin Flask |
| `validation.py` | Validación pura de payloads v1 |
| `auth.py` | Esquemas de autorización y hashes |
| `navigation.py` | Proyección, sentido y ETA independientes de HTTP/SQL |
| `seed_routes.py` | Importación idempotente de Línea 2 |
| `dev_simulator.py` | Orquestación optativa de aprovisionamiento y envío HTTP |

Las lecturas sencillas de rutas/alertas llaman repositorios directamente: no se añaden servicios vacíos. Vehículos usa un servicio porque combina datos y navegación. Se mantienen los límites transaccionales originales, incluida la inserción de telemetría y actualización de estado juntas.

`API_Global.py` y los exports públicos de `api_utils.py` son wrappers de compatibilidad. El factory canónico continúa siendo `backend.app:create_app()`.

## Frontend

| Módulo | Responsabilidad |
| --- | --- |
| `main.py` | Arranque Flet CLI o módulo Python |
| `views/passenger.py` | Pantalla y eventos |
| `components/` | Controles reutilizables sin acceso a API |
| `models.py` | Rutas y snapshots inmutables |
| `state.py` | Estado por página y seguimiento de cámara |
| `config.py` | Entorno y parámetros visuales |
| `presentation.py` | Formato ETA, rumbo y llegada demo |
| `services/` | Assets locales, adaptadores REST y composición de fuentes |
| `theme.py` | Tokens visuales |

Imports mediante el paquete `app`; solo el entrypoint directo añade la raíz al path. Tests desde la raíz. GeoJSON permanece en `app/assets/routes/`: evita duplicación y cambios innecesarios al empaquetado. Docker copia únicamente esos assets del frontend.

## Infraestructura

Compose sigue en raíz, proyecto `zentryx`, servicios `db/api/simulator`, perfil `demo` y volumen lógico `zentryx_db`. Esquema y migraciones no cambian. No se agregan microservicios, ORM o infraestructura adicional.

## Hardware y firmware

`hardware/silice/` contiene el proyecto KiCad activo del dispositivo Silice: esquemático, PCB, símbolos, footprints y modelos 3D. Es independiente del runtime Python/Docker y conserva rutas internas relativas mediante `${KIPRJMOD}`.

`prototypes/firmware/` queda reservado para el futuro código que se ejecute en el dispositivo físico (microcontrolador/GPS). Hasta entonces, `backend/dev_simulator.py` sustituye el productor de telemetría real.

Los archivos temporales y cachés de KiCad no forman parte de las fuentes del proyecto y están excluidos por `.gitignore`.

## Deuda pendiente, por prioridad

1. Historial automático de migraciones, respaldos y prueba de restauración: requiere coordinación operativa.
2. Retención de telemetría e índices basados en carga real.
3. Geometría duplicada entre navegación y demos: unificación pendiente de equivalencia numérica.
4. Polling REST y herencia del adaptador API desde la fuente demo: evaluar composición al incorporar hardware.
5. La pantalla aún concentra bindings Flet; dividir más cuando exista otra pantalla real.
6. Lock completo de dependencias transitivas y retiro de wrappers cuando se descarten consumidores externos.
7. GeoJSON exprés y prototipos conservados; no representan servicios activos o implementaciones completas.

La validación eléctrica/DRC del proyecto KiCad sigue siendo una tarea de hardware y no forma parte de la suite Python/CI actual.
