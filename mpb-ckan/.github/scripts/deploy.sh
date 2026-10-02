#!/bin/bash
set -e

cd "$(dirname "$0")/../.."

echo "Authenticating Docker to Artifact Registry..."
source .env
GAR_HOST="$(echo "${REGISTRY}" | cut -d'/' -f1)"
ACCESS_TOKEN=$(curl -sf "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token" -H "Metadata-Flavor: Google" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "${ACCESS_TOKEN}" | docker login -u oauth2accesstoken --password-stdin "https://${GAR_HOST}"

echo "Pulling images and starting services..."
docker compose -f docker-compose.yml pull ckan nginx db
docker compose -f docker-compose.yml up -d --remove-orphans

docker image prune -f
echo "Deploy complete."