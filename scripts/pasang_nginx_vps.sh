#!/usr/bin/env bash
# Pasang Nginx + SSL Let's Encrypt di VPS Ubuntu
# Jalankan DI VPS sebagai root/sudo setelah docker compose up
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: sudo bash scripts/pasang_nginx_vps.sh wargio.domain.com"
  exit 1
fi

DOMAIN="$1"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONF_SRC="${ROOT}/deploy/nginx/wargio.conf.example"
CONF_DST="/etc/nginx/sites-available/wargio"

if [[ ! -f "${CONF_SRC}" ]]; then
  echo "GAGAL: ${CONF_SRC} tidak ada"
  exit 1
fi

echo "=== Pasang paket nginx + certbot ==="
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y nginx certbot python3-certbot-nginx

echo "=== Salin config Nginx ==="
sed "s/wargio.contohdomain.com/${DOMAIN}/g" "${CONF_SRC}" > "/tmp/wargio.nginx.conf"
cp "/tmp/wargio.nginx.conf" "${CONF_DST}"
ln -sf "${CONF_DST}" /etc/nginx/sites-enabled/wargio
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

echo "=== Test & reload nginx (HTTP dulu) ==="
nginx -t
systemctl enable nginx
systemctl reload nginx

echo "=== Certbot SSL ==="
certbot --nginx -d "${DOMAIN}" --non-interactive --agree-tos -m "admin@${DOMAIN}" || {
  echo "Certbot butuh email — jalankan manual:"
  echo "  certbot --nginx -d ${DOMAIN}"
  exit 1
}

nginx -t && systemctl reload nginx

echo ""
echo "OK: Nginx + SSL untuk https://${DOMAIN}"
echo "Verifikasi: curl -s https://${DOMAIN}/api/health | head -c 200"
