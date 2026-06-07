#!/usr/bin/env bash
# Tampilkan IP publik VPS untuk Atlas Network Access allowlist
set -euo pipefail

echo "=== IP publik server ini (untuk Atlas allowlist) ==="
IP=$(curl -sf https://api.ipify.org || curl -sf https://ifconfig.me/ip || true)
if [[ -z "${IP}" ]]; then
  echo "GAGAL: tidak bisa deteksi IP publik"
  exit 1
fi

echo "IP: ${IP}"
echo ""
echo "Langkah Atlas:"
echo "  1. MongoDB Atlas → Network Access → Add IP Address"
echo "  2. Masukkan: ${IP}/32"
echo "  3. Tunggu ~1 menit, lalu curl /api/health → atlas:true"
