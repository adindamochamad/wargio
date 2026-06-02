# Wargio — AI Agent for Indonesia's Micro-Retailers

> Built for [Google Cloud Rapid Agent Hackathon 2026](https://rapid-agent.devpost.com/) | MongoDB Track

## What is Wargio?

Wargio is an AI business assistant for Indonesian warung owners. Ask in natural Bahasa Indonesia — stock, debts, sales — and the agent reasons over live data in MongoDB Atlas via MCP, then takes action (not just answers).

## Demo

- Video: _(YouTube link — coming Hari 7)_
- **Live app:** _(isi URL VPS Anda setelah deploy, contoh `https://wargio.domain.com`)_

## Architecture

```
User → Next.js (VPS) → FastAPI (VPS) → Gemini / intent engine → MongoDB Atlas (MCP-equivalent)
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Agent | Google Cloud Agent Builder, Gemini 3 |
| Data | MongoDB Atlas M0, MongoDB MCP Server |
| API | Python 3.11+, FastAPI, PyMongo Async, Pydantic v2 |
| Frontend | Next.js App Router, TypeScript, Tailwind |
| Deploy | **VPS** (Docker + Nginx + HTTPS) — lihat [docs/deploy-vps.md](docs/deploy-vps.md) |

## MongoDB Integration

- Collections: `products`, `transactions`, `customers`, `agent_sessions`
- Vector search on `products.name` (768d, cosine) for fuzzy product matching
- MCP tools: `find`, `aggregate`, `insertOne`, `updateOne`

## Local Development

### Prerequisites

- Python 3.11+
- MongoDB Atlas cluster + connection string
- _(Hari 2+)_ Google Cloud project, Agent Builder

### Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp ../.env.example ../.env
# Edit ../.env with your MONGODB_URI

# Indexes + seed (first time)
python ../scripts/buat_indeks.py
python ../scripts/buat_vector_index.py --bebaskan-slot-sample
python ../scripts/seed_data.py

# Verify Day 1 (semua gate, termasuk vector index + GitHub public)
python ../scripts/verifikasi_hari1.py
# atau: npm run verifikasi:hari1

# Run API
uvicorn app.main:aplikasi --reload --host 0.0.0.0 --port 8000
```

Health check: `curl http://localhost:8000/api/health`

### Frontend (Hari 4)

```bash
# Terminal 1 — API (restart otomatis, MCP off untuk UI cepat)
bash scripts/jalankan_dev.sh
# atau manual:
# cd backend && MCP_LIVE_ENABLED=false uvicorn app.main:aplikasi --reload --port 8000

# Terminal 2 — UI (mode proxy, tanpa CORS)
cd frontend
cp .env.example .env.local   # biarkan NEXT_PUBLIC_API_URL kosong
npm install
npm run dev
```

Buka http://localhost:3000.

**Tips performa:** `MCP_LIVE_ENABLED=false` di `.env` root (default) — chat UI responsif.

**Verifikasi Hari 4:** `npm run verifikasi:hari4` (butuh API hidup di port 8000).

## Production (VPS — Hari 5)

Panduan lengkap: **[docs/deploy-vps.md](docs/deploy-vps.md)**

```bash
cp deploy/.env.production.example deploy/.env.production
# Edit: MONGODB_URI, CORS_ORIGINS, WARGIO_PUBLIC_URL

bash scripts/deploy_vps.sh          # di VPS setelah git pull
# Pasang Nginx + certbot (lihat deploy/nginx/wargio.conf.example)

export WARGIO_PRODUCTION_URL=https://domain-anda.com
bash scripts/smoke_production.sh
npm run verifikasi:hari5
```

## Environment Variables

See [`.env.example`](.env.example). Never commit `.env`.

## Running Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest ../tests -v

# Verifikasi per hari (gate DoD)
python ../scripts/verifikasi_hari1.py
python ../scripts/verifikasi_hari3.py
python ../scripts/verifikasi_hari4.py
python ../scripts/verifikasi_hari5.py
```

## License

MIT — see [LICENSE](LICENSE).
