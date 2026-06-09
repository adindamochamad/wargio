#!/usr/bin/env bash
# Verifikasi satu perintah untuk judge — smoke production + petunjuk MCP
set -euo pipefail

URL="${WARGIO_PRODUCTION_URL:-https://wargio.adindamochamad.com}"
URL="${URL%/}"

echo "=== Wargio Judge Verify ==="
echo "URL: ${URL}"
echo ""

echo "--- Health ---"
curl -s "${URL}/api/health" | python3 -m json.tool
echo ""

export WARGIO_PRODUCTION_URL="${URL}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
bash "${ROOT}/scripts/smoke_production.sh"

echo ""
echo "=== MCP tools (jalan di mesin dengan MONGODB_URI) ==="
echo "  npm run verifikasi:mcp"
echo "  npm run verifikasi:mcp-live   # opsional: pool stdio live"
echo ""
echo "=== UI ==="
echo "  Buka ${URL} — toggle EN (judge) di header"
echo ""
echo "=== Judge Verify: LOLOS ==="
