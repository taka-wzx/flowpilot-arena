#!/bin/sh
set -eu

: "${TEMPORAL_ADDRESS:?TEMPORAL_ADDRESS is required}"
: "${DEFAULT_NAMESPACE:?DEFAULT_NAMESPACE is required}"

if temporal operator namespace describe \
  --address "$TEMPORAL_ADDRESS" \
  --namespace "$DEFAULT_NAMESPACE" >/dev/null 2>&1; then
  exit 0
fi

temporal operator namespace create \
  --address "$TEMPORAL_ADDRESS" \
  --namespace "$DEFAULT_NAMESPACE" \
  --retention 1d
