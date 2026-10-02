#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

FAKE_BIN="${TMP_DIR}/bin"
mkdir -p "${FAKE_BIN}"

cat > "${FAKE_BIN}/docker" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "${FAKE_DOCKER_LOG}"
EOF
chmod +x "${FAKE_BIN}/docker"

export FAKE_DOCKER_LOG="${TMP_DIR}/docker.log"
PATH="${FAKE_BIN}:${PATH}" "${ROOT}/bin/daily-restart"

grep -Eq '^compose -f .*/docker-compose\.yml down$' "${FAKE_DOCKER_LOG}"
grep -Eq '^compose -f .*/docker-compose\.yml up -d --wait$' "${FAKE_DOCKER_LOG}"

for script in "${ROOT}"/bin/* "${ROOT}"/ckan/docker-entrypoint.d/*.sh "${ROOT}"/postgresql/docker-entrypoint-initdb.d/*.sh; do
  bash -n "${script}"
done

test ! -d "${ROOT}/mpb-ckan"
test -f "${ROOT}/.env.example"

echo "Operational shell checks passed."
