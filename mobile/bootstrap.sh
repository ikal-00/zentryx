#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v flutter >/dev/null 2>&1; then
  echo "Flutter no está instalado o no está en PATH." >&2
  exit 1
fi

if [[ ! -d ios || ! -d android ]]; then
  flutter create . \
    --platforms=ios,android \
    --org com.zentryx \
    --project-name zentryx_mobile
fi

flutter pub get
flutter analyze
flutter test

echo "Zentryx Mobile listo. Ejecuta: flutter run"
