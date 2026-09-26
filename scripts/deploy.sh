#!/usr/bin/env bash
# Called only by CD in the existing server checkout; preserves .env and volumes.
set -euo pipefail

EXPECTED_SHA="${1:?Pass the full commit SHA that passed CI}"
if [[ ! "$EXPECTED_SHA" =~ ^[0-9a-f]{40}$ ]]; then
  echo "Invalid commit SHA" >&2
  exit 1
fi
cd /home/miner3/zentryx
git fetch origin main
if [[ "$(git rev-parse origin/main)" != "$EXPECTED_SHA" ]]; then
  echo "main changed since this CI run; waiting for the newer run to deploy." >&2
  exit 1
fi
git reset --hard "$EXPECTED_SHA"
docker compose config --quiet
docker compose --profile demo up -d --build --remove-orphans
docker compose --profile demo ps
for attempt in {1..12}; do
  if python3 scripts/check_shared_api.py; then
    exit 0
  fi
  echo "API not ready (attempt ${attempt}/12)."
  sleep 5
done
docker compose --profile demo logs --tail=150 api
exit 1
