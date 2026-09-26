# Arquitectura

## Flujo real

Los clientes consumen la misma API `/v1`. Flutter es el cliente móvil nativo y Flet permanece como respaldo durante la transición. Ambos leen ruta/estaciones, unidad y alertas sin acceder directamente a PostgreSQL. En una desconexión conservan el último estado válido; el backend sigue siendo la autoridad de navegación y ETA.

El simulador compartido aprovisiona dispositivo, unidad y alerta demo en PostgreSQL. Luego publica `/v1/telemetry` con token efímero. La API valida, autentica y guarda idempotentemente. La lectura de vehículos combina última muestra, historial reciente, proyección sobre ruta y próxima estación.

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

## Cliente móvil Flutter

`mobile/` implementa el MVP de pasajero para iOS y Android sin duplicar lógica de backend.

| Módulo | Responsabilidad |
| --- | --- |
| `lib/app/` | App, tema global y lifecycle |
| `lib/core/config/` | URL de API, IDs y cadencias |
| `lib/core/network/` | Cliente HTTP y traducción de errores |
| `lib/design_system/` | Tokens, superficies y marca Zentryx |
| `lib/features/transit/domain/` | Modelos del contrato API v1 |
| `lib/features/transit/data/` | Repositorio y caché estática |
| `lib/features/transit/application/` | Estado, polling, pausa y reanudación |
| `lib/features/transit/presentation/` | Mapa, HUD, ruta, estaciones y animaciones |

La ruta y las estaciones se cachean durante la sesión. La unidad y las alertas se consultan cada 2 s; la posición y el heading se interpolan visualmente entre muestras. El polling se pausa en segundo plano y se refresca al volver para limitar uso de batería y red.

`Zentryx Mobile CI` ejecuta analyzer, tests y builds de Android debug e iOS simulator. La retirada definitiva de Flet requiere una prueba manual corta en dispositivos reales; el detalle está en `mobile/PARITY.md`.

## Cliente Flet de respaldo

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

Compose sigue en raíz, proyecto `zentryx`, servicios `db/api/simulator`, perfil `demo` y volumen lógico `zentryx_db`. Esquema y migraciones no cambian. Tailscale proporciona acceso privado desde los clientes al servidor compartido. No se agregan microservicios, ORM o infraestructura adicional.

## Hardware y firmware

`hardware/silice/` contiene el proyecto KiCad activo del dispositivo Silice: esquemático, PCB, símbolos, footprints y modelos 3D. Es independiente del runtime Python/Docker y conserva rutas internas relativas mediante `${KIPRJMOD}`.

`prototypes/firmware/` queda reservado para el futuro código que se ejecute en el dispositivo físico (microcontrolador/GPS). Hasta entonces, `backend/dev_simulator.py` sustituye el productor de telemetría real.

Los archivos temporales y cachés de KiCad no forman parte de las fuentes del proyecto y están excluidos por `.gitignore`.

## Deuda pendiente, por prioridad

1. Historial automático de migraciones, respaldos y prueba de restauración: requiere coordinación operativa.
2. Retención de telemetría e índices basados en carga real.
3. Geometría duplicada entre navegación y demos: unificación pendiente de equivalencia numérica.
4. Evolucionar polling REST a tiempo real cuando el contrato `/v1/realtime` esté definido y justificado.
5. Retirar Flet solo después de validar Flutter en hardware iOS/Android real.
6. Lock completo de dependencias transitivas y retiro de wrappers cuando se descarten consumidores externos.
7. GeoJSON exprés y prototipos conservados; no representan servicios activos o implementaciones completas.

La validación eléctrica/DRC del proyecto KiCad sigue siendo una tarea de hardware y no forma parte de la suite de software actual.
