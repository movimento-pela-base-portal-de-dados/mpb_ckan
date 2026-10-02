#!/bin/bash
set -e

REGISTRY="${1:?REGISTRY argument required}"

docker compose build ckan nginx db
docker compose push ckan nginx db