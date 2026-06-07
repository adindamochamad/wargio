#!/usr/bin/env bash
# Orkestrator Hari 5 — siapkan env, build Docker, panduan deploy VPS
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

LANGKAH="${1:-all}"

case "${LANGKAH}" in
  env)
    bash scripts/siapkan_env_production.sh "${2:-}"
    ;;
  build)
    bash scripts/siapkan_env_production.sh "${2:-http://127.0.0.1}" 2>/dev/null || true
    if [[ ! -f deploy/.env.production ]]; then
      bash scripts/siapkan_env_production.sh
    fi
    docker compose -f deploy/docker/docker-compose.yml \
      --env-file deploy/.env.production build
    ;;
  up)
    docker compose -f deploy/docker/docker-compose.yml \
      --env-file deploy/.env.production up -d
    sleep 10
    curl -sf http://127.0.0.1:8000/api/health && echo ""
    ;;
  smoke-lokal)
    export WARGIO_PRODUCTION_URL="${WARGIO_PRODUCTION_URL:-http://127.0.0.1:8000}"
    bash scripts/smoke_production.sh
    ;;
  deploy-vps)
    bash scripts/deploy_vps.sh
    ;;
  nginx)
    sudo bash scripts/pasang_nginx_vps.sh "${2:?Usage: selesaikan_hari5.sh nginx DOMAIN}"
    ;;
  atlas-ip)
    bash scripts/cek_ip_vps_atlas.sh
    ;;
  k6)
    bash scripts/jalankan_k6_production.sh
    ;;
  verifikasi)
    backend/.venv/bin/python scripts/verifikasi_hari5.py
    ;;
  all)
    echo "=== Hari 5 Wargio — urutan deploy ==="
    echo ""
    echo "Di laptop (sebelum SSH ke VPS):"
    echo "  1. bash scripts/selesaikan_hari5.sh env https://DOMAIN-ANDA.com"
    echo "  2. git push"
    echo ""
    echo "Di VPS:"
    echo "  3. git clone / git pull"
    echo "  4. bash scripts/selesaikan_hari5.sh env https://DOMAIN-ANDA.com"
    echo "  5. bash scripts/selesaikan_hari5.sh deploy-vps"
    echo "  6. bash scripts/selesaikan_hari5.sh atlas-ip  → allowlist di Atlas"
    echo "  7. sudo bash scripts/selesaikan_hari5.sh nginx DOMAIN-ANDA.com"
    echo ""
    echo "Dari laptop (setelah HTTPS hidup):"
    echo "  8. export WARGIO_PRODUCTION_URL=https://DOMAIN-ANDA.com"
    echo "  9. bash scripts/selesaikan_hari5.sh smoke-lokal"
    echo " 10. bash scripts/selesaikan_hari5.sh k6"
    echo " 11. bash scripts/selesaikan_hari5.sh verifikasi"
    echo ""
    bash scripts/selesaikan_hari5.sh verifikasi
    ;;
  *)
    echo "Usage: selesaikan_hari5.sh [env|build|up|smoke-lokal|deploy-vps|nginx|atlas-ip|k6|verifikasi|all] [domain]"
    exit 1
    ;;
esac
