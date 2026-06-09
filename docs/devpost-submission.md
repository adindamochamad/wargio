# Devpost — Wargio (Google Cloud Rapid Agent Hackathon 2026)

> **MongoDB Track** | Form: https://rapid-agent.devpost.com/

## Copy-paste cepat

| Field Devpost | Nilai |
|---------------|-------|
| **Project name** | Wargio |
| **Tagline** | AI agent for Indonesia's 64 million micro-retailers |
| **Elevator pitch** | Wargio lets Indonesian warung owners manage stock, debt, and sales in natural language — powered by live MongoDB Atlas and Google Gemini. |
| **Partner track** | **MongoDB** |
| **Project URL** | https://wargio.adindamochamad.com |
| **Source code URL** | https://github.com/adindamochamad/wargio |
| **License** | MIT |
| **Demo video** | _(YouTube URL — paste after upload)_ |
| **Built with** | MongoDB, MongoDB MCP Server, Google Cloud, Gemini, Agent Engine, Python, FastAPI, Next.js, TypeScript, Docker |

### Tags (suggested)

`MongoDB` `Google Cloud` `Gemini` `Python` `Next.js` `MCP` `FastAPI` `Indonesia` `AI Agent`

---

## Verifikasi untuk judge (1 perintah)

```bash
git clone https://github.com/adindamochamad/wargio.git && cd wargio
export WARGIO_PRODUCTION_URL=https://wargio.adindamochamad.com
bash scripts/judge_verify.sh
```

Di browser: buka live URL → klik **EN** di header → coba **Check Stock**.

MCP tools (clone repo + `MONGODB_URI`):

```bash
npm run verifikasi:mcp
```

---

## Deskripsi proyek (paste ke form Devpost)

### Inspiration

64 million micro-retailers in Indonesia still run shops on memory and handwritten debt books. We built Wargio so owners can ask "how much Indomie stock is left?" or "who still owes money?" and get answers from **live data** — then record sales with one confirmation.

### What it does

- **Check stock** with fuzzy product names (aliases + vector search)
- **Record sales** → confirms → updates stock + transaction in Atlas
- **Debt tracking** → list debtors, record payments
- **Business insights** → daily/weekly revenue, restock alerts, day-of-week forecast
- **Bahasa Indonesia** default + **English mode** for international judges

### How we built it

- **Frontend:** Next.js, SSR dashboard prefetch, ID/EN i18n, dark mode
- **Backend:** FastAPI orchestration, 8 intents, atomic writes
- **AI:** Gemini 2.5 Flash for classification; regex fallback for deterministic write intents
- **Google Agent Engine:** ADK agent deployed (`AGENT_ENGINE_ID`)
- **MongoDB Atlas:** products, transactions, customers; vector index 768d
- **MCP:** `find`, `aggregate`, `insertOne`, `updateOne` — verified via `mongodb-mcp-server`; production uses equivalent `atlas_tools` layer for UI latency

### Challenges

- Fuzzy Indonesian product names ("aqua", "indomie goreng")
- Write safety — confirmation before any Atlas mutation
- Balancing MCP stdio latency vs production responsiveness

### Accomplishments

- Live production URL with 8 intents + write path
- 83% backend test coverage, k6 p95 < 3s
- English + Indonesian UI for global judges

### What we learned

Document model + aggregation pipelines fit warung data better than rigid SQL schemas. Vector search handles messy product aliases.

### What's next

Multi-warung tenancy, WhatsApp channel, voice input for hands-busy shop owners.

---

## Checklist submit

- [ ] Login Devpost → edit submission
- [x] Project URL live
- [x] Repo public + MIT
- [ ] Demo video YouTube (~3 min, EN subtitles)
- [ ] Paste video URL ke Devpost + README
- [ ] Track = MongoDB
- [ ] Submit before **11 Juni 2026, 14:00 PDT**
