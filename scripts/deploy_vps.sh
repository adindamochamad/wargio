#!/usr/bin/env bash
# Helper deploy di VPS — jalankan di server setelah git pull
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

if [[ ! -f deploy/.env.production ]]; then
  echo "Buat deploy/.env.production dari deploy/.env.production.example"
  exit 1
fi

echo "=== Build & up Docker Compose ==="
docker compose -f deploy/docker/docker-compose.yml \
  --env-file deploy/.env.production \
  up -d --build

echo ""
echo "=== Tunggu health API ==="
sleep 8
curl -sf http://127.0.0.1:8000/api/health | head -c 120 || {
  echo "API belum ready — cek: docker compose -f deploy/docker/docker-compose.yml logs api"
  exit 1
}

echo ""
echo "=== Langkah berikutnya ==="
echo "1. Pasang Nginx: deploy/nginx/wargio.conf.example"
echo "2. certbot --nginx"
echo "3. export WARGIO_PRODUCTION_URL=https://domain-anda && bash scripts/smoke_production.sh"
