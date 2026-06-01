#!/usr/bin/env bash
# Selesaikan item partial Hari 1: seed besar, MCP, verifikasi, vector index (jika slot tersedia)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${ROOT}/backend/.venv/bin/python"
PROJECT_ID="6a01e8d9024c5dde708d8aa1"
CLUSTER="Cluster0"

echo "=== 1/4 Seed expanded ==="
"$PY" scripts/seed_data.py

echo "=== 2/4 Vector index (M0 max 1 — skip jika penuh) ==="
if atlas clusters search indexes create --clusterName "$CLUSTER" --projectId "$PROJECT_ID" \
  --file scripts/products_vector_index.json -o json 2>/dev/null; then
  echo "OK: Vector index dibuat"
else
  echo "SKIP: Vector index — M0 mungkin sudah punya 1 index (buat manual di Atlas UI jika perlu)"
fi

echo "=== 3/4 MCP verifikasi ==="
npm run verifikasi:mcp

echo "=== 4/4 Verifikasi Hari 1 ==="
"$PY" scripts/verifikasi_hari1.py

echo "=== Partial Hari 1: SELESAI ==="
