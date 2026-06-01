# Wargio — AI Agent for Indonesia's Micro-Retailers

> Built for [Google Cloud Rapid Agent Hackathon 2026](https://rapid-agent.devpost.com/) | MongoDB Track

## What is Wargio?

Wargio is an AI business assistant for Indonesian warung owners. Ask in natural Bahasa Indonesia — stock, debts, sales — and the agent reasons over live data in MongoDB Atlas via MCP, then takes action (not just answers).

## Demo

- Video: _(YouTube link — coming Hari 7)_
- Live app: _(URL — coming Hari 5)_

## Architecture

```
User → Next.js → FastAPI (Cloud Run) → Agent Builder (Gemini 3) → MongoDB MCP → Atlas
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Agent | Google Cloud Agent Builder, Gemini 3 |
| Data | MongoDB Atlas M0, MongoDB MCP Server |
| API | Python 3.11+, FastAPI, PyMongo Async, Pydantic v2 |
| Frontend | Next.js App Router, TypeScript, Tailwind _(Hari 4)_ |
| Deploy | Cloud Run, Vercel |

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
python ../scripts/seed_data.py

# Verify Day 1
python ../scripts/verifikasi_hari1.py

# Run API
uvicorn app.main:aplikasi --reload --host 0.0.0.0 --port 8000
```

Health check: `curl http://localhost:8000/api/health`

## Environment Variables

See [`.env.example`](.env.example). Never commit `.env`.

## Running Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest ../tests -v
```

## License

MIT — see [LICENSE](LICENSE).
