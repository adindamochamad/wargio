#!/usr/bin/env bash
# Smoke test URL production — set WARGIO_PRODUCTION_URL=https://domain-anda.com
set -euo pipefail

URL="${WARGIO_PRODUCTION_URL:-}"
if [[ -z "${URL}" ]]; then
  echo "GAGAL: export WARGIO_PRODUCTION_URL=https://domain-anda.com"
  exit 1
fi

URL="${URL%/}"
echo "=== Smoke production: ${URL} ==="

cek() {
  local path="$1"
  local harapan="$2"
  local code
  code=$(curl -s -o /tmp/wargio_smoke_body.txt -w "%{http_code}" "${URL}${path}")
  if [[ "${code}" != "${harapan}" ]]; then
    echo "GAGAL: ${path} HTTP ${code} (harapkan ${harapan})"
    head -c 200 /tmp/wargio_smoke_body.txt
    exit 1
  fi
  echo "OK: ${path} → ${code}"
}

cek "/api/health" "200"
cek "/api/dashboard" "200"

SID="smoke-$(date +%s)"
res=$(curl -s -X POST "${URL}/api/chat" \
  -H "Content-Type: application/json" \
  -H "X-Session-Id: ${SID}" \
  -d '{"pesan":"stok indomie goreng berapa?"}')
echo "${res}" | grep -q check_stock && echo "OK: chat check_stock" || {
  echo "GAGAL: chat intent"
  echo "${res}" | head -c 300
  exit 1
}

echo "=== Smoke production: LOLOS ==="
