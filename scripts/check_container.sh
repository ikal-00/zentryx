#!/usr/bin/env bash
# Run only in a disposable CI project, never in the shared server project.
set -euo pipefail
if [[ "${COMPOSE_PROJECT_NAME:-}" != "zentryx-ci" || "${GITHUB_ACTIONS:-}" != "true" ]]; then
  echo "This runtime check requires the disposable zentryx-ci GitHub Actions project." >&2
  exit 1
fi

wait_for_api() {
  for attempt in {1..30}; do
    if python3 scripts/check_shared_api.py http://127.0.0.1:5000; then
      return 0
    fi
    sleep 2
  done
  return 1
}

docker compose config --quiet
docker compose --profile demo up -d --build
wait_for_api
# Check data, not only the volume declaration: record a row across DB recreation.
row_before="$(docker compose exec -T db psql -U zentryx -d zentryx -Atc 'SELECT MIN(id) FROM telemetry;')"
[[ "$row_before" =~ ^[0-9]+$ ]]
docker compose --profile demo stop
docker compose up -d --force-recreate db
docker compose --profile demo up -d
wait_for_api
row_after="$(docker compose exec -T db psql -U zentryx -d zentryx -Atc 'SELECT MIN(id) FROM telemetry;')"
test "$row_before" = "$row_after"
echo "PostGIS persistence verified across database container recreation."
