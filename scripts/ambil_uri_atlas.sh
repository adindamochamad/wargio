#!/usr/bin/env bash
# Ambil connection string Atlas via CLI, lalu update .env (password DB diisi manual)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${ROOT}/.env"

if ! command -v atlas >/dev/null 2>&1; then
  echo "Install: brew install mongodb-atlas-cli"
  exit 1
fi

if ! atlas auth whoami >/dev/null 2>&1; then
  echo "Sesi Atlas expired. Jalankan di terminal kamu:"
  echo "  atlas auth login"
  echo "Lalu jalankan lagi: bash scripts/ambil_uri_atlas.sh"
  exit 1
fi

echo "=== Projects ==="
atlas projects list

echo ""
read -r -p "Project ID (hex): " PROJECT_ID
read -r -p "Nama cluster: " CLUSTER_NAME
read -r -p "Database user: " DB_USER
read -s -p "Database password: " DB_PASS
echo ""

JSON=$(atlas clusters connectionStrings describe "$CLUSTER_NAME" --projectId "$PROJECT_ID" -o json)
# Ambil SRV standard (jq jika ada)
if command -v jq >/dev/null 2>&1; then
  BASE=$(echo "$JSON" | jq -r '.connectionStrings.standardSrv // .standardSrv // empty' | head -1)
else
  BASE=$(echo "$JSON" | grep -oE 'mongodb\+srv://[^"]+' | head -1)
fi

if [[ -z "$BASE" ]]; then
  echo "Gagal parse URI dari Atlas CLI. Output disimpan ke /tmp/atlas-conn.json"
  echo "$JSON" > /tmp/atlas-conn.json
  exit 1
fi

# Sisipkan user:pass setelah mongodb+srv://
HOSTPATH=$(echo "$BASE" | sed -E 's|^mongodb\+srv://||')
# URL-encode password sederhana (@ -> %40)
DB_PASS_ENC=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$DB_PASS''', safe=''))")

FULL_URI="mongodb+srv://${DB_USER}:${DB_PASS_ENC}@${HOSTPATH}"
# Pastikan ada database di path
if [[ "$FULL_URI" != *"/wargio_demo"* ]]; then
  FULL_URI=$(echo "$FULL_URI" | sed 's|/?|/wargio_demo?|' | sed 's|\?retry|/wargio_demo?retry|')
fi

if grep -q '^MONGODB_URI=' "$ENV_FILE" 2>/dev/null; then
  if [[ "$(uname)" == "Darwin" ]]; then
    sed -i '' "s|^MONGODB_URI=.*|MONGODB_URI=${FULL_URI}|" "$ENV_FILE"
  else
    sed -i "s|^MONGODB_URI=.*|MONGODB_URI=${FULL_URI}|" "$ENV_FILE"
  fi
else
  echo "MONGODB_URI=${FULL_URI}" >> "$ENV_FILE"
fi

grep -q '^MONGODB_DATABASE=' "$ENV_FILE" || echo "MONGODB_DATABASE=wargio_demo" >> "$ENV_FILE"

echo "OK: .env diupdate (MONGODB_URI tidak ditampilkan di log)."
echo "Jalankan: bash scripts/jalankan_hari1.sh"
