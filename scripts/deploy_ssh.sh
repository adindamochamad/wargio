#!/usr/bin/env bash
# Deploy ke VPS via SSH — jalankan dari laptop
# Usage: bash scripts/deploy_ssh.sh user@1.2.3.4 https://wargio.domain.com
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: bash scripts/deploy_ssh.sh user@host https://domain.com [path-repo-di-vps]"
  exit 1
fi

SSH_TARGET="$1"
DOMAIN="$2"
REMOTE_DIR="${3:-~/wargio}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Deploy Wargio ke ${SSH_TARGET} ==="
echo "Domain: ${DOMAIN}"
echo "Repo VPS: ${REMOTE_DIR}"

# Pastikan env production ada lokal (untuk referensi, tidak di-upload otomatis)
if [[ ! -f "${ROOT}/deploy/.env.production" ]]; then
  bash "${ROOT}/scripts/siapkan_env_production.sh" "${DOMAIN}"
fi

echo ""
echo "=== Sync repo (git pull di VPS) ==="
ssh "${SSH_TARGET}" "test -d ${REMOTE_DIR}/.git || git clone https://github.com/adindamochamad/wargio.git ${REMOTE_DIR}"
ssh "${SSH_TARGET}" "cd ${REMOTE_DIR} && git pull --ff-only"

echo ""
echo "=== Upload deploy/.env.production (sekali) ==="
scp "${ROOT}/deploy/.env.production" "${SSH_TARGET}:${REMOTE_DIR}/deploy/.env.production"

echo ""
echo "=== Docker compose up ==="
ssh "${SSH_TARGET}" "cd ${REMOTE_DIR} && bash scripts/deploy_vps.sh"

echo ""
echo "=== IP untuk Atlas allowlist ==="
ssh "${SSH_TARGET}" "cd ${REMOTE_DIR} && bash scripts/cek_ip_vps_atlas.sh"

echo ""
echo "=== Langkah manual di VPS ==="
echo "  ssh ${SSH_TARGET}"
echo "  cd ${REMOTE_DIR} && sudo bash scripts/pasang_nginx_vps.sh ${DOMAIN#https://}"
echo ""
echo "Lalu dari laptop:"
echo "  export WARGIO_PRODUCTION_URL=${DOMAIN}"
echo "  bash scripts/smoke_production.sh"
echo "  bash scripts/jalankan_k6_production.sh"
