#!/usr/bin/env bash
# Load test k6 10 VU — catat hasil ke docs/hari5-load-test.md
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
URL="${WARGIO_PRODUCTION_URL:-}"
if [[ -z "${URL}" ]]; then
  echo "GAGAL: export WARGIO_PRODUCTION_URL=https://domain-anda.com"
  exit 1
fi

if ! command -v k6 >/dev/null 2>&1; then
  echo "GAGAL: k6 belum terpasang — https://grafana.com/docs/k6/latest/set-up/install-k6/"
  exit 1
fi

URL="${URL%/}"
STAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
OUT="${ROOT}/docs/hari5-load-test.md"
LOG="/tmp/wargio_k6_${STAMP}.log"

echo "=== k6 smoke 10 users → ${URL} ==="
k6 run -e "BASE_URL=${URL}" "${ROOT}/deploy/k6/smoke_10_users.js" 2>&1 | tee "${LOG}"

# Ekstrak p95 dari output k6
P95=$(grep -E "http_req_duration.*p\(95\)" "${LOG}" | tail -1 || true)

cat > "${OUT}" <<EOF
# Hari 5 — Load Test k6

| Field | Nilai |
|-------|-------|
| Waktu (UTC) | ${STAMP} |
| URL | ${URL} |
| Skrip | deploy/k6/smoke_10_users.js |
| VU | 10 |
| Durasi | 30s |
| Threshold | p95 < 5000ms, checks > 90% |

## Hasil

\`\`\`
${P95:-(lihat log k6)}
\`\`\`

## Log lengkap

\`\`\`
$(tail -40 "${LOG}")
\`\`\`

DoD: p95 response < 5 detik untuk 10 concurrent users.
EOF

echo ""
echo "OK: Laporan disimpan → ${OUT}"
