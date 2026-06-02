#!/usr/bin/env bash
# Hari 1 — index, seed, verifikasi (butuh .env dengan URI Atlas asli)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${ROOT}/backend/.venv/bin/python"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Dibuat .env dari template — EDIT MONGODB_URI dulu, lalu jalankan lagi."
  exit 1
fi

if grep -qE 'USER:|PASSWORD@|<password>' .env 2>/dev/null; then
  echo "Blocker: MONGODB_URI di .env masih placeholder."
  echo "  1. Buka https://cloud.mongodb.com → Connect → Drivers"
  echo "  2. Copy URI, paste ke .env (ganti password)"
  echo "  3. Jalankan lagi: bash scripts/jalankan_hari1.sh"
  exit 1
fi

echo "=== buat_indeks ==="
"$PY" scripts/buat_indeks.py
echo "=== buat_vector_index ==="
"$PY" scripts/buat_vector_index.py --bebaskan-slot-sample
echo "=== seed_data ==="
"$PY" scripts/seed_data.py
echo "=== verifikasi_hari1 ==="
"$PY" scripts/verifikasi_hari1.py
echo "=== Hari 1 script pipeline: LOLOS ==="
