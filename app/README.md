# Zentryx · interfaz móvil

## Ejecutar

Desde la raíz del repositorio, con el entorno existente:

```bash
cd app
source .venv/bin/activate
flet run --web main.py
```

Si falta alguna dependencia, `python -m pip install -r requirements.txt` instala
las versiones verificadas (Flet 1.0.0 y flet-map 1.0.0). Para un entorno nuevo,
crea primero `.venv` con `python3 -m venv .venv`.

Para abrirla en un teléfono conectado a la misma red local:

```bash
flet run --web --host '*' --port 8550 main.py
```

Abre `http://IP_LOCAL_DE_TU_COMPUTADORA:8550` en el teléfono. Los mosaicos de
OpenStreetMap necesitan conexión a internet. El GeoJSON se resuelve relativo
a `main.py`, sin depender del directorio desde el que se importe el módulo.

## Organización

- `main.py`: composición, selección de estaciones, cámara y consumo del servicio.
- `components/passenger.py`: cabecera, controles, tarjeta de unidad/estación y banner.
- `theme.py`: colores, dimensiones, sombras y configuración de Flet.
- `services/`: fuente de datos existente, sin modificaciones.
- `assets/`: geografía original, sin modificaciones.

El mapa conserva ruta, movimiento, rumbo y seguimiento cada seis snapshots.
Arrastrar o ampliar manualmente libera la cámara; centrar vuelve a seguir la
última posición. Tocar una estación abre su ficha y libera la cámara. Cerrar
la ficha regresa a la tarjeta de unidad sin mover el mapa; centrar también
cierra la ficha y reanuda el seguimiento.

La tarjeta inferior mide como máximo 460 px. En ventanas de menos de 560 px
de alto tiene desplazamiento vertical para conservar un área útil de mapa.
Los botones principales tienen zonas táctiles de 48–52 px y etiquetas accesibles.

## Datos actuales y futura integración

`VehicleService` todavía genera el recorrido de demostración original. La UI
muestra **Datos de demostración** y no afirma que la unidad sea GPS en vivo.
No se agregaron vehículos, estaciones, saturación ni incidentes simulados.

Se preserva el cálculo existente de próxima estación: proyección sobre la ruta,
sentido, tolerancia de 15 m y distancia / velocidad. La presentación del ETA
usa minutos redondeados hacia arriba o `<1 min`; detenido sin ETA muestra `—`.
No es una predicción de tráfico ni incorpora tiempos de parada.

Cuando se conecte la API:

- Sustituir el adaptador de datos manteniendo la interfaz de snapshots y cambiar
  `demo_source` en `main.py`. Un `online` se presenta como **Unidad conectada**,
  no como confirmación del estado general del servicio.
- `low`, `medium`, `high` tienen etiquetas de ocupación; `unknown` se oculta.
- `AlertBanner.set_alert(payload)` acepta un aviso real activo con `message`
  y `severity` (`info`, `warning`, `critical`), según `/contracts/api_v1.md`.
  El adaptador debe filtrar el aviso por ruta/unidad antes de suministrarlo y
  llamar a `page.update()`. El banner queda oculto cuando no hay datos.
- Las fichas de estación usan únicamente el nombre del GeoJSON. No presentan
  unidades acercándose, ETAs ni estados inventados; falta integrar ese servicio.
- Las coordenadas y el rumbo permanecen en los snapshots y en el mapa, sin
  ocupar espacio en la tarjeta del pasajero.

Backend, BD, firmware y contratos no se modifican.

## Validación

Desde `app`:

```bash
python -m unittest discover -s tests -v
python -m compileall -q main.py components theme.py
```

Se verificaron seis pruebas: cambio de seguimiento por gestos, centrado,
selección de estación, actualización de marcador y rumbo, ETA en ambos sentidos
y casos detenido/terminal, datos ausentes/alertas, geografía y tamaños de ventana.
Los tests usan controles Flet reales; la llamada de cámara al cliente se sustituye
por un mock. No reemplazan la comprobación visual.

También se arrancó `flet run --web main.py` y se verificaron HTTP 200 para la
página y el GeoJSON. Se inspeccionó la UI en Chromium a 390×844, 320×568,
844×390 y 1440×900, y se probaron arrastre, centrado, selección y cierre de ficha.
La red del entorno de validación no permitió cargar los mosaicos externos de
OpenStreetMap: se comprobó el render de ruta y marcadores, pero la cartografía
base requiere comprobación final en una red con acceso a ese proveedor.
