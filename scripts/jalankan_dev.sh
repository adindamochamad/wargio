#!/usr/bin/env bash
# Dev stack: API terbaru (port 8000) + petunjuk frontend
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${ROOT}/backend/.venv/bin/python"
PORT="${WARGIO_API_PORT:-8000}"

echo "=== Hentikan proses lama di port ${PORT} (jika ada) ==="
if lsof -ti:"${PORT}" >/dev/null 2>&1; then
  lsof -ti:"${PORT}" | xargs kill -9 2>/dev/null || true
  sleep 1
  echo "OK: Port ${PORT} dibebaskan"
fi

export MCP_LIVE_ENABLED="${MCP_LIVE_ENABLED:-false}"

echo "=== Jalankan FastAPI (MCP_LIVE_ENABLED=${MCP_LIVE_ENABLED}) ==="
echo "Dashboard: http://127.0.0.1:${PORT}/api/dashboard"
echo "Health:    http://127.0.0.1:${PORT}/api/health"
echo ""
echo "Frontend (terminal lain):"
echo "  cd frontend && npm run dev"
echo ""

cd "${ROOT}/backend"
exec env MCP_LIVE_ENABLED="${MCP_LIVE_ENABLED}" \
  "${PY}" -m uvicorn app.main:aplikasi --reload --host 127.0.0.1 --port "${PORT}"
