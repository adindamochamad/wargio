#!/usr/bin/env bash
# Smoke test URL production — 4 intent Tier 1 + health + dashboard
set -euo pipefail

URL="${WARGIO_PRODUCTION_URL:-}"
if [[ -z "${URL}" ]]; then
  echo "GAGAL: export WARGIO_PRODUCTION_URL=https://domain-anda.com"
  exit 1
fi

URL="${URL%/}"
echo "=== Smoke production: ${URL} ==="

cek_http() {
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

cek_http "/api/health" "200"

if ! grep -q '"atlas":true' /tmp/wargio_smoke_body.txt && ! grep -q '"atlas": true' /tmp/wargio_smoke_body.txt; then
  echo "GAGAL: /api/health atlas!=true — cek MONGODB_URI & IP VPS di Atlas allowlist"
  cat /tmp/wargio_smoke_body.txt
  exit 1
fi
echo "OK: atlas=true"

cek_http "/api/dashboard" "200"

SID="smoke-$(date +%s)"

cek_intent() {
  local pesan="$1"
  local harapan="$2"
  local res
  res=$(curl -s -X POST "${URL}/api/chat" \
    -H "Content-Type: application/json" \
    -H "X-Session-Id: ${SID}" \
    -d "{\"pesan\":\"${pesan}\"}")
  if echo "${res}" | grep -q "\"intent\":\"${harapan}\""; then
    echo "OK: intent ${harapan}"
  else
    echo "GAGAL: chat '${harapan}' — respons:"
    echo "${res}" | head -c 400
    exit 1
  fi
}

cek_intent "stok indomie goreng berapa?" "check_stock"
cek_intent "hutang Bu Sari berapa?" "check_debt"
cek_intent "berapa pendapatan hari ini?" "sales_report"
cek_intent "produk apa yang mau habis?" "restock_alert"

# UI root (Next.js) — skip jika smoke hanya ke port API
if [[ "${URL}" == *":8000"* ]]; then
  echo "INFO: skip UI / — smoke ke port API saja"
else
  code_root=$(curl -s -o /tmp/wargio_smoke_root.txt -w "%{http_code}" "${URL}/")
  if [[ "${code_root}" != "200" ]]; then
    echo "GAGAL: / HTTP ${code_root} — frontend tidak hidup"
    exit 1
  fi
  echo "OK: / → 200 (frontend)"
fi

echo "=== Smoke production: LOLOS (health + dashboard + 4 intent + UI) ==="
