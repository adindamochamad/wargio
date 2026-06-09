#!/usr/bin/env bash
# Latihan query demo video Hari 7 — jalankan sebelum screen record.
# Semua request ke production; pastikan atlas=true.
# Bahasa: WARGIO_DEMO_LANG=en (default, sesuai script video) atau id
set -euo pipefail

URL="${WARGIO_PRODUCTION_URL:-https://wargio.adindamochamad.com}"
URL="${URL%/}"
PREFIX="rehearsal-video-$(date +%s)"
BAHASA="${WARGIO_DEMO_LANG:-en}"

echo "=== Rehearsal demo video: ${URL} ==="
echo "Sesi prefix: ${PREFIX}"
echo "Bahasa demo: ${BAHASA}"
echo ""

post_chat() {
  local pesan="$1"
  local sid="$2"
  local label="$3"
  local code body intent
  local header_bahasa=()

  if [[ -n "${BAHASA}" ]]; then
    header_bahasa=(-H "X-Wargio-Language: ${BAHASA}")
  fi

  code=$(curl -s -o /tmp/wargio_rehearsal.json -w "%{http_code}" \
    -X POST "${URL}/api/chat" \
    -H "Content-Type: application/json" \
    -H "X-Session-Id: ${sid}" \
    "${header_bahasa[@]}" \
    -d "{\"pesan\":\"${pesan}\"}")

  if [[ "${code}" == "429" ]]; then
    echo "  WARN 429 — tunggu 3s, retry"
    sleep 3
    sid="${sid}-r"
    code=$(curl -s -o /tmp/wargio_rehearsal.json -w "%{http_code}" \
      -X POST "${URL}/api/chat" \
      -H "Content-Type: application/json" \
      -H "X-Session-Id: ${sid}" \
      "${header_bahasa[@]}" \
      -d "{\"pesan\":\"${pesan}\"}")
  fi

  body=$(cat /tmp/wargio_rehearsal.json)
  intent=$(echo "${body}" | grep -o '"intent":"[^"]*"' | head -1 || true)

  if [[ "${code}" != "200" ]]; then
    echo "GAGAL [${label}] HTTP ${code}"
    echo "${body}" | head -c 400
    exit 1
  fi

  echo "OK [${label}] ${intent}"
  echo "  → ${pesan}"
  echo "  balasan: $(echo "${body}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('balasan','')[:120].replace(chr(10),' '))" 2>/dev/null || head -c 120 /tmp/wargio_rehearsal.json)"
  echo ""
  sleep 0.5
}

# Health
code=$(curl -s -o /tmp/wargio_health.json -w "%{http_code}" "${URL}/api/health")
if [[ "${code}" != "200" ]]; then
  echo "GAGAL: /api/health HTTP ${code}"
  exit 1
fi
if ! grep -qE '"atlas"\s*:\s*true' /tmp/wargio_health.json; then
  echo "GAGAL: atlas tidak true"
  cat /tmp/wargio_health.json
  exit 1
fi
echo "OK: health atlas=true"
echo ""

if [[ "${BAHASA}" == "en" ]]; then
  post_chat "how much indomie goreng stock is left?" "${PREFIX}-stock" "scene2_stock"

  SID_SALE="${PREFIX}-sale"
  post_chat "sold 2 indomie goreng and 1 air mineral aqua 600ml" "${SID_SALE}" "scene3_sale_draft"
  post_chat "yes" "${SID_SALE}" "scene3_sale_confirm"

  SID_DEBT="${PREFIX}-debt"
  post_chat "who still owes money this week?" "${SID_DEBT}" "scene4_debt_list"
  post_chat "Bu Sari paid debt 50000" "${SID_DEBT}" "scene4_payment_draft"
  post_chat "yes" "${SID_DEBT}" "scene4_payment_confirm"

  post_chat "what is this week's revenue?" "${PREFIX}-insight" "scene5_sales_report"
  post_chat "will it be busy tomorrow?" "${PREFIX}-forecast" "scene5_forecast"
else
  post_chat "stok indomie goreng berapa?" "${PREFIX}-stock" "scene2_stock"

  SID_SALE="${PREFIX}-sale"
  post_chat "tadi jual 2 indomie goreng dan 1 air mineral aqua 600ml" "${SID_SALE}" "scene3_sale_draft"
  post_chat "ya" "${SID_SALE}" "scene3_sale_confirm"

  SID_DEBT="${PREFIX}-debt"
  post_chat "siapa yang belum bayar hutang minggu ini?" "${SID_DEBT}" "scene4_debt_list"
  post_chat "Bu Sari bayar hutang 50000" "${SID_DEBT}" "scene4_payment_draft"
  post_chat "ya" "${SID_DEBT}" "scene4_payment_confirm"

  post_chat "berapa pendapatan minggu ini?" "${PREFIX}-insight" "scene5_sales_report"
  post_chat "kira-kira besok bakal ramai?" "${PREFIX}-forecast" "scene5_forecast"
fi

echo "=== Rehearsal demo video: LOLOS ==="
echo "Siap rekam. Gunakan sesi INCOGNITO + toggle EN (jika en) saat take final."
