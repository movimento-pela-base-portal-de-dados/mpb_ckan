#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for script in "${ROOT}"/bin/* "${ROOT}"/ckan/docker-entrypoint.d/*.sh "${ROOT}"/ckan/setup/*.sh "${ROOT}"/postgresql/docker-entrypoint-initdb.d/*.sh; do
  bash -n "${script}"
done

test ! -d "${ROOT}/mpb-ckan"
test -f "${ROOT}/.env.example"

echo "Operational shell checks passed."
