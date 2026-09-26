# Zentryx · interfaz móvil

## Setup

Desde la raíz:

```bash
make setup
```

El launcher reconoce tanto `app/.venv` antiguo como el `.venv` recomendado en la raíz.

## Servidor compartido

```bash
bash app/run_shared_api.sh
```

Valores por defecto:

```text
ZENTRYX_API_BASE_URL=http://100.72.215.34:5000
ZENTRYX_SERVICE_ID=l2-ordinary
ZENTRYX_VEHICLE_ID=unit-demo-01
```

Puedes sobrescribir las variables antes de iniciar.

## Modo demo local y modo API

Sin `ZENTRYX_API_BASE_URL`, `main.py` usa `VehicleService` como simulación local.

En modo API:

- ruta y estaciones vienen del backend;
- posición y heading vienen de `/v1/vehicles/{id}`;
- próxima estación y ETA son autoridad del backend;
- alertas vienen de `/v1/alerts`;
- `direction=unknown` no se convierte artificialmente en ida;
- si la API cae, la interfaz conserva la última posición conocida.

Si la definición de ruta no está disponible durante el arranque, el mapa puede usar el asset local como fallback visual.

## Organización

| Ubicación | Responsabilidad |
| --- | --- |
| `main.py` | Entry point Flet |
| `views/` y `components/` | Pantalla y controles |
| `models.py`, `state.py`, `config.py` | Datos, seguimiento y entorno |
| `presentation.py`, `theme.py` | Formato y estilos |
| `services/` | Fuentes y adaptadores REST |
| `assets/routes/` | GeoJSON local |
| `tests/` | Interacciones y contratos de adapters |

`assets/routes/` funciona como fallback y fuente de seed para Línea 2. El servicio ordinario mantiene 43 estaciones de La Quebrada a Las Américas.

## Seguimiento del mapa

El marcador se actualiza con cada snapshot. La cámara limita actualizaciones por tiempo/distancia para evitar jitter. Mover el mapa activa exploración libre y el botón de centrado reactiva seguimiento.

## Tests

```bash
python -m unittest discover -s app/tests -v
python -m compileall -q app
```

O desde la raíz:

```bash
make verify
```

Contrato: `../contracts/api_v1.md`  
Esquema: `../database/schema.sql`
