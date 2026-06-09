#!/usr/bin/env bash
# Smoke test URL production — 8 intent + write path + health + dashboard
set -euo pipefail

URL="${WARGIO_PRODUCTION_URL:-}"
if [[ -z "${URL}" ]]; then
  echo "GAGAL: export WARGIO_PRODUCTION_URL=https://domain-anda.com"
  exit 1
fi

URL="${URL%/}"
PREFIX_SID="smoke-$(date +%s)-$$"
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

# POST chat dengan retry 1x jika rate limit (429)
post_chat() {
  local pesan="$1"
  local sid="$2"
  local bahasa="${3:-}"
  local code body
  local header_bahasa=()
  if [[ -n "${bahasa}" ]]; then
    header_bahasa=(-H "X-Wargio-Language: ${bahasa}")
  fi
  code=$(curl -s -o /tmp/wargio_smoke_chat.txt -w "%{http_code}" -X POST "${URL}/api/chat" \
    -H "Content-Type: application/json" \
    -H "X-Session-Id: ${sid}" \
    "${header_bahasa[@]}" \
    -d "{\"pesan\":\"${pesan}\"}")
  if [[ "${code}" == "429" ]]; then
    echo "  WARN: HTTP 429 — tunggu 2s, retry dengan sesi baru"
    sleep 2
    sid="${sid}-retry"
    code=$(curl -s -o /tmp/wargio_smoke_chat.txt -w "%{http_code}" -X POST "${URL}/api/chat" \
      -H "Content-Type: application/json" \
      -H "X-Session-Id: ${sid}" \
      "${header_bahasa[@]}" \
      -d "{\"pesan\":\"${pesan}\"}")
  fi
  body=$(cat /tmp/wargio_smoke_chat.txt)
  echo "${code}"$'\n'"${body}"
}

cek_intent() {
  local pesan="$1"
  local harapan="$2"
  local sid="${PREFIX_SID}-${harapan}"
  local bahasa="${3:-}"
  local hasil code res

  hasil=$(post_chat "${pesan}" "${sid}" "${bahasa}")
  code=$(echo "${hasil}" | head -n1)
  res=$(echo "${hasil}" | tail -n +2)

  if [[ "${code}" != "200" ]]; then
    echo "GAGAL: chat '${harapan}' HTTP ${code}"
    echo "${res}" | head -c 400
    exit 1
  fi
  if echo "${res}" | grep -q "\"intent\":\"${harapan}\""; then
    echo "OK: intent ${harapan}"
  else
    echo "GAGAL: chat '${harapan}' — respons:"
    echo "${res}" | head -c 400
    exit 1
  fi
  sleep 0.3
}

cek_http "/api/health" "200"

if ! grep -q '"atlas":true' /tmp/wargio_smoke_body.txt && ! grep -q '"atlas": true' /tmp/wargio_smoke_body.txt; then
  echo "GAGAL: /api/health atlas!=true — cek MONGODB_URI & IP VPS di Atlas allowlist"
  cat /tmp/wargio_smoke_body.txt
  exit 1
fi
echo "OK: atlas=true"

if grep -q '"mcp_tools"' /tmp/wargio_smoke_body.txt; then
  echo "OK: health mencantumkan mcp_tools"
fi

cek_http "/api/dashboard" "200"

# Tier 1 read
cek_intent "stok indomie goreng berapa?" "check_stock"
cek_intent "hutang Bu Sari berapa?" "check_debt"
cek_intent "berapa pendapatan hari ini?" "sales_report"
cek_intent "produk apa yang mau habis?" "restock_alert"

# Tier 2 read
cek_intent "siapa yang belum bayar hutang minggu ini?" "debt_collection"
cek_intent "kira-kira besok bakal ramai?" "sales_forecast"

# English (judge)
cek_intent "how much indomie goreng stock is left?" "check_stock" "en"

# Write path — record_sale (qty kecil, sesi terpisah)
SID_SALE="${PREFIX_SID}-record_sale"
hasil_sale=$(post_chat "jual 1 indomie goreng" "${SID_SALE}")
code_sale=$(echo "${hasil_sale}" | head -n1)
res_sale=$(echo "${hasil_sale}" | tail -n +2)
if [[ "${code_sale}" != "200" ]]; then
  echo "GAGAL: record_sale draft HTTP ${code_sale}"
  exit 1
fi
if echo "${res_sale}" | grep -q '"intent":"record_sale"'; then
  echo "OK: intent record_sale (draft)"
else
  echo "GAGAL: record_sale draft — tidak ada intent"
  exit 1
fi
hasil_confirm=$(post_chat "ya" "${SID_SALE}")
code_confirm=$(echo "${hasil_confirm}" | head -n1)
res_confirm=$(echo "${hasil_confirm}" | tail -n +2)
if [[ "${code_confirm}" != "200" ]]; then
  echo "GAGAL: record_sale confirm HTTP ${code_confirm}"
  exit 1
fi
if echo "${res_confirm}" | grep -qiE "berhasil|successfully|recorded"; then
  echo "OK: record_sale (confirmed write)"
else
  echo "GAGAL: record_sale confirm — balasan tidak sukses"
  echo "${res_confirm}" | head -c 300
  exit 1
fi

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
  if curl -sI "${URL}/icon.svg" | head -1 | grep -q "200"; then
    echo "OK: /icon.svg → favicon"
  fi
fi

echo "=== Smoke production: LOLOS (8 intent + write + EN + UI) ==="
