#!/usr/bin/env bash
set -euo pipefail

# The base image runs prerun.py, which loads every plugin in CKAN__PLUGINS,
# before /docker-entrypoint.d. Local extensions must be installed first.
for extension in "${SRC_EXTENSIONS_DIR:-/srv/app/src_extensions}"/*/; do
  if [[ -f "${extension}setup.py" || -f "${extension}pyproject.toml" ]]; then
    echo "Installing extension ${extension}"
    pip install --quiet -e "${extension}"
  fi
done

exec /srv/app/start_ckan_development.sh "$@"
