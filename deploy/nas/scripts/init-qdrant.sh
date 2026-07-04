#!/usr/bin/env sh
set -eu

QDRANT_HOST="${QDRANT_HOST:-127.0.0.1}"
QDRANT_HTTP_PORT="${QDRANT_HTTP_PORT:-6333}"
QDRANT_API_KEY="${QDRANT_API_KEY:-}"
EMBEDDING_DIM="${EMBEDDING_DIM:-1536}"
MEMORY_COLLECTION="${QDRANT_MEMORY_COLLECTION:-novel_memory_chunks}"
REFERENCE_COLLECTION="${QDRANT_REFERENCE_COLLECTION:-novel_reference_chunks}"

header_args=""
if [ -n "$QDRANT_API_KEY" ]; then
  header_args="-H api-key:${QDRANT_API_KEY}"
fi

create_collection() {
  name="$1"
  curl -sS -X PUT "http://${QDRANT_HOST}:${QDRANT_HTTP_PORT}/collections/${name}" \
    $header_args \
    -H "Content-Type: application/json" \
    --data "{\"vectors\":{\"size\":${EMBEDDING_DIM},\"distance\":\"Cosine\"}}"
  printf "\n"
}

create_collection "$MEMORY_COLLECTION"
create_collection "$REFERENCE_COLLECTION"

