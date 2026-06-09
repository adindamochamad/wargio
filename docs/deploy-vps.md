# Deploy Wargio di VPS (Hari 5)

Panduan ini menggantikan Cloud Run + Vercel untuk submission. Yang wajib hackathon: **URL HTTPS live** yang bisa dibuka judge, bukan platform tertentu.

## Arsitektur disarankan

```text
Internet :443 (HTTPS)
    └── Nginx (SSL Let's Encrypt)
            ├── /          → Next.js :3010 (host) → :3000 (container)
            └── /api/*     → FastAPI :8000
MongoDB Atlas (cloud, tetap di luar VPS)
```

Satu domain contoh: `https://wargio.contohdomain.com`  
API lewat path sama: `https://wargio.contohdomain.com/api/health`

## Prasyarat VPS

- Ubuntu 22.04+ (atau setara)
- Docker + Docker Compose plugin
- Domain mengarah A record ke IP VPS
- Port 80/443 terbuka
- Atlas Network Access: **izinkan IP VPS** (bukan hanya laptop Anda)

## Langkah cepat (Docker Compose)

### 1. Clone & env production

```bash
git clone https://github.com/adindamochamad/wargio.git
cd wargio

# Otomatis dari .env lokal (salin .env dulu jika perlu)
bash scripts/siapkan_env_production.sh https://wargio.contohdomain.com

# Manual alternatif:
# cp deploy/.env.production.example deploy/.env.production
# nano deploy/.env.production
```

**Penting VPS:** set `MCP_LIVE_ENABLED=false`. Untuk Gemini di Docker, isi `GEMINI_API_KEY` (ADC `gcloud` tidak ada di container).

### 2. Build & jalankan

```bash
bash scripts/deploy_vps.sh
# atau: bash scripts/selesaikan_hari5.sh deploy-vps
```

### 3. Atlas allowlist IP VPS

```bash
bash scripts/cek_ip_vps_atlas.sh
# Tambahkan IP/32 di Atlas Network Access
```

### 4. Nginx + SSL di host

```bash
sudo bash scripts/pasang_nginx_vps.sh wargio.contohdomain.com
# atau manual: deploy/nginx/wargio.conf.example + certbot
```

### 5. Verifikasi dari laptop

```bash
export WARGIO_PRODUCTION_URL=https://wargio.contohdomain.com
bash scripts/smoke_production.sh      # health + 4 intent + UI
bash scripts/jalankan_k6_production.sh  # p95 → docs/hari5-load-test.md
python scripts/verifikasi_hari5.py
```

### Deploy dari laptop via SSH

```bash
bash scripts/deploy_ssh.sh user@ip-vps https://wargio.contohdomain.com
```

## Variabel production penting

| Variabel | Contoh | Catatan |
|----------|--------|---------|
| `MONGODB_URI` | `mongodb+srv://...` | Wajib, jangan commit |
| `MONGODB_DATABASE` | `wargio_demo` | |
| `CORS_ORIGINS` | `https://wargio.contohdomain.com` | Domain frontend HTTPS |
| `MCP_LIVE_ENABLED` | `false` | UI cepat |
| `GEMINI_API_KEY` | `...` | Opsional; fallback regex |
| `RATE_LIMIT_PER_MINUTE` | `30` | Per sesi/IP |
| `WARGIO_PUBLIC_URL` | `https://wargio.contohdomain.com` | README & build frontend |
| `NEXT_PUBLIC_API_URL` | kosong atau URL publik | Kosong = same-origin `/api` |

## Checklist Hari 5 (VPS)

- [x] `deploy/.env.production` terisi (tidak di git)
- [x] Atlas allowlist IP VPS (`45.76.156.99/32`)
- [x] `docker compose up` — api + web healthy (web host `:3010`)
- [x] Nginx HTTPS aktif
- [x] `curl https://DOMAIN/api/health` → `"atlas":true`
- [x] `curl https://DOMAIN/api/dashboard` → JSON
- [x] UI: 4 quick action Tier 1 tanpa error
- [x] `scripts/verifikasi_hari5.py` lolos
- [x] README: Live URL di bagian Demo
- [x] Devpost: Live URL siap — `docs/devpost-submission.md` (paste ke form Devpost)

## Troubleshooting

| Gejala | Solusi |
|--------|--------|
| Dashboard 404 | Rebuild image API terbaru; cek route `/api/dashboard` |
| CORS error di browser | Sesuaikan `CORS_ORIGINS` dengan domain HTTPS tepat |
| Chat lambat | `MCP_LIVE_ENABLED=false`, restart api |
| Atlas gagal | Cek IP VPS di Network Access |
| 502 Bad Gateway | `docker compose ps`; cek log `docker compose logs api` |
| `/` HTTP 400 "Invalid Host header" | Port host 3000 bentrok — cek `ss -tlnp \| grep 3000`; gunakan map `3010:3000` di compose |

## Tanpa Docker (manual)

```bash
# API
cd backend && pip install -r requirements.txt
MCP_LIVE_ENABLED=false uvicorn app.main:aplikasi --host 127.0.0.1 --port 8000

# Frontend (terminal lain)
cd frontend && npm ci && npm run build
NEXT_PUBLIC_API_URL= npm start -p 3000
```

Nginx tetap proxy `127.0.0.1:3000` dan `127.0.0.1:8000`.
