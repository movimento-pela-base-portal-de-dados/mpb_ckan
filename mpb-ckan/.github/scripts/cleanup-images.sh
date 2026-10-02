#!/bin/bash
set -e

REGISTRY="${1:?REGISTRY argument required}"

for SERVICE in ckan nginx db; do
  # Sort images by createTime descending (newest first)
  DIGESTS=$(gcloud artifacts docker images list "${REGISTRY}/${SERVICE}" \
    --format="csv[no-heading](createTime,version)" \
    | sort -r \
    | awk -F',' '{print $2}')

  COUNT=0
  for DIGEST in $DIGESTS; do
    [ -z "$DIGEST" ] && continue
    COUNT=$((COUNT + 1))
    if [ "$COUNT" -eq 1 ]; then
      gcloud artifacts docker tags add \
        "${REGISTRY}/${SERVICE}@${DIGEST}" \
        "${REGISTRY}/${SERVICE}:latest" --quiet
    elif [ "$COUNT" -eq 2 ]; then
      gcloud artifacts docker tags add \
        "${REGISTRY}/${SERVICE}@${DIGEST}" \
        "${REGISTRY}/${SERVICE}:previous" --quiet
    else
      gcloud artifacts docker images delete \
        "${REGISTRY}/${SERVICE}@${DIGEST}" --quiet || true
    fi
  done
done
