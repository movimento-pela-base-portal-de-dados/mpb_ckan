#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="mpbckanvalidacao"
PROBE_FILE="$(mktemp)"
COMPOSE_FILE="${ROOT}/docker-compose.dev.yml"

if docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
elif [[ "$(docker-compose version --short 2>/dev/null)" == 2.* ]]; then
  COMPOSE=(docker-compose)
else
  echo "Docker Compose V2 não encontrado." >&2
  exit 1
fi

if [[ ! -f "${ROOT}/.env" ]]; then
  echo "Arquivo .env ausente. Execute: cp .env.example .env" >&2
  exit 1
fi

cat > "${PROBE_FILE}" <<'EOF'
services:
  storage-probe:
    image: busybox:1.36
    command: ["sh", "-c", "sleep 3600"]
    volumes:
      - ckan_storage:/data
    restart: "no"
EOF

cleanup() {
  "${COMPOSE[@]}" -p "${PROJECT}" --env-file "${ROOT}/.env.example" \
    -f "${COMPOSE_FILE}" -f "${PROBE_FILE}" down -v --remove-orphans >/dev/null 2>&1 || true
  rm -f "${PROBE_FILE}"
}
trap cleanup EXIT

compose() {
  "${COMPOSE[@]}" -p "${PROJECT}" --env-file "${ROOT}/.env.example" \
    -f "${COMPOSE_FILE}" -f "${PROBE_FILE}" "$@"
}

require_healthy() {
  local service="$1"
  local container status
  container="$(compose ps -q "${service}")"
  status="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "${container}")"
  if [[ "${status}" != "healthy" ]]; then
    echo "Serviço ${service} ficou ${status}." >&2
    compose logs --tail=80 "${service}" >&2 || true
    exit 1
  fi
}

echo "Subindo db, solr, redis e o volume do CKAN..."
compose up -d --wait --build db solr redis storage-probe
require_healthy db
require_healthy solr
require_healthy redis

compose exec -T db psql -v ON_ERROR_STOP=1 --username postgres --dbname postgres \
  -c "CREATE TABLE persist_probe(id integer PRIMARY KEY); INSERT INTO persist_probe VALUES (1);"
compose exec -T solr sh -c 'echo persist-ok > /var/solr/persist_probe.txt'
compose exec -T storage-probe sh -c 'echo persist-ok > /data/persist_probe.txt'

echo "Recriando containers sem apagar volumes..."
compose down --remove-orphans
compose up -d --wait db solr redis storage-probe
require_healthy db
require_healthy solr
require_healthy redis

db_value="$(compose exec -T db psql -v ON_ERROR_STOP=1 --username postgres --dbname postgres -tAc 'SELECT id FROM persist_probe')"
solr_value="$(compose exec -T solr sh -c 'cat /var/solr/persist_probe.txt')"
storage_value="$(compose exec -T storage-probe sh -c 'cat /data/persist_probe.txt')"

[[ "${db_value}" == "1" ]] || { echo "PostgreSQL perdeu o dado: ${db_value}" >&2; exit 1; }
[[ "${solr_value}" == "persist-ok" ]] || { echo "Solr perdeu o dado: ${solr_value}" >&2; exit 1; }
[[ "${storage_value}" == "persist-ok" ]] || { echo "ckan_storage perdeu o dado: ${storage_value}" >&2; exit 1; }

echo "Persistência validada: pg_data, solr_data e ckan_storage sobrevivem ao down."
