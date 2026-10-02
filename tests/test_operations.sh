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

DEPLOY_ROOT="${TMP_DIR}/deploy"
mkdir -p "${DEPLOY_ROOT}/.github/scripts" "${DEPLOY_ROOT}/bin"
cp "${ROOT}/.github/scripts/deploy.sh" "${DEPLOY_ROOT}/.github/scripts/deploy.sh"
printf 'REGISTRY=registry.example.org/abc\n' > "${DEPLOY_ROOT}/.env"

cat > "${FAKE_BIN}/curl" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' '{"access_token":"test-token"}'
EOF

cat > "${FAKE_BIN}/python3" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' 'test-token'
EOF
chmod +x "${FAKE_BIN}/curl" "${FAKE_BIN}/python3"

(cd "${DEPLOY_ROOT}" && PATH="${FAKE_BIN}:${PATH}" bash .github/scripts/deploy.sh)
grep -Eq '^login -u oauth2accesstoken --password-stdin https://registry\.example\.org$' "${FAKE_DOCKER_LOG}"
grep -Fxq 'compose -f docker-compose.yml pull ckan nginx db' "${FAKE_DOCKER_LOG}"
grep -Fxq 'compose -f docker-compose.yml up -d --remove-orphans' "${FAKE_DOCKER_LOG}"
grep -Fxq 'image prune -f' "${FAKE_DOCKER_LOG}"

for script in "${ROOT}"/bin/* "${ROOT}"/.github/scripts/*.sh; do
  bash -n "${script}"
done

echo "Operational shell checks passed."
