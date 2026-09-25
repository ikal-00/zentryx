#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

if ! command -v flet >/dev/null 2>&1; then
  echo "Flet no está instalado en este entorno. Activa app/.venv o instala app/requirements.txt." >&2
  exit 1
fi

export ZENTRYX_API_BASE_URL="${ZENTRYX_API_BASE_URL:-http://100.72.215.34:5000}"
export ZENTRYX_SERVICE_ID="${ZENTRYX_SERVICE_ID:-l2-ordinary}"
export ZENTRYX_VEHICLE_ID="${ZENTRYX_VEHICLE_ID:-unit-demo-01}"

printf 'Zentryx API: %s\n' "$ZENTRYX_API_BASE_URL"
printf 'Servicio: %s · Unidad: %s\n' "$ZENTRYX_SERVICE_ID" "$ZENTRYX_VEHICLE_ID"

exec flet run --web main.py
