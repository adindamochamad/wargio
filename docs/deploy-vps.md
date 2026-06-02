# Deploy Wargio di VPS (Hari 5)

Panduan ini menggantikan Cloud Run + Vercel untuk submission. Yang wajib hackathon: **URL HTTPS live** yang bisa dibuka judge, bukan platform tertentu.

## Arsitektur disarankan

```text
Internet :443 (HTTPS)
    └── Nginx (SSL Let's Encrypt)
            ├── /          → Next.js :3000
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
cp deploy/.env.production.example deploy/.env.production
nano deploy/.env.production   # isi MONGODB_URI, GEMINI_API_KEY, domain, dll.
```

### 2. Build & jalankan

```bash
cd deploy/docker
docker compose --env-file ../.env.production up -d --build
```

Layanan internal: `api` (8000), `web` (3000). Nginx di host (lihat bawah) atau tambah container `nginx`.

### 3. Nginx + SSL di host

```bash
sudo cp deploy/nginx/wargio.conf.example /etc/nginx/sites-available/wargio
# Edit server_name dan path proxy
sudo ln -s /etc/nginx/sites-available/wargio /etc/nginx/sites-enabled/
sudo certbot --nginx -d wargio.contohdomain.com
sudo nginx -t && sudo systemctl reload nginx
```

### 4. Verifikasi

```bash
# Dari laptop
export WARGIO_PRODUCTION_URL=https://wargio.contohdomain.com
python scripts/verifikasi_hari5.py
bash scripts/smoke_production.sh
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

- [ ] `deploy/.env.production` terisi (tidak di git)
- [ ] Atlas allowlist IP VPS
- [ ] `docker compose up` — api + web healthy
- [ ] Nginx HTTPS aktif
- [ ] `curl https://DOMAIN/api/health` → `"atlas":true`
- [ ] `curl https://DOMAIN/api/dashboard` → JSON
- [ ] UI: 4 quick action Tier 1 tanpa error
- [ ] `scripts/verifikasi_hari5.py` lolos
- [ ] README: Live URL di bagian Demo
- [ ] Devpost: URL production

## Troubleshooting

| Gejala | Solusi |
|--------|--------|
| Dashboard 404 | Rebuild image API terbaru; cek route `/api/dashboard` |
| CORS error di browser | Sesuaikan `CORS_ORIGINS` dengan domain HTTPS tepat |
| Chat lambat | `MCP_LIVE_ENABLED=false`, restart api |
| Atlas gagal | Cek IP VPS di Network Access |
| 502 Bad Gateway | `docker compose ps`; cek log `docker compose logs api` |

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
