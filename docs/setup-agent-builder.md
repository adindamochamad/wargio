# Setup Google Cloud Agent Builder + Gemini (Hari 2)

## Status Deploy Wargio

| Field | Value |
|-------|-------|
| Project | `tessera-496904` |
| Region | `us-central1` |
| Model | `gemini-2.5-flash` |
| Agent Engine ID | `7738092906182868992` |
| Playground | [Vertex AI Agent Engine](https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/us-central1/agent-engines/7738092906182868992/playground?project=976178971698) |

## Prasyarat

1. Google Cloud project dengan **billing aktif**
2. API enabled: `aiplatform.googleapis.com`
3. ADC: `gcloud auth application-default login`

## Konfigurasi `.env`

```bash
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT=tessera-496904
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-flash
AGENT_ENGINE_ID=7738092906182868992
MONGODB_URI=...
MONGODB_DATABASE=wargio_demo
```

## Deploy via CLI (ADK)

```bash
# Install ADK (sekali)
cd backend && pip install google-adk google-cloud-aiplatform

# Test lokal
export $(grep -v '^#' .env | xargs)
backend/.venv/bin/adk run agent/wargio "stok indomie berapa?"

# Deploy ke Agent Engine
backend/.venv/bin/python scripts/deploy_agent_engine.py
# atau langsung:
backend/.venv/bin/adk deploy agent_engine agent/wargio \
  --project=tessera-496904 \
  --region=us-central1 \
  --display_name=wargio \
  --env_file=.env
```

## Struktur Agent ADK

```
agent/wargio/
├── agent.py          # root_agent + 4 tools
├── tools.py          # MCP-equivalent find/aggregate
├── prompts/          # system prompt Wargio
└── requirements.txt
```

## Tools (MCP mapping)

| Tool ADK | Intent | MCP |
|----------|--------|-----|
| `cek_stok_produk` | check_stock | find products |
| `cek_hutang_customer` | check_debt | find customers |
| `daftar_restock_alert` | restock_alert | find + sort |
| `laporan_penjualan` | sales_report | aggregate transactions |

## Verifikasi

```bash
curl http://localhost:8000/api/health
# agent_mode: gemini, gemini_configured: true

backend/.venv/bin/adk run agent/wargio "hutang Bu Sari berapa?"
```

## Mode Fallback FastAPI

Jika Agent Engine tidak dipanggil, FastAPI `/api/chat` tetap jalan dengan intent engine + Gemini classification.
