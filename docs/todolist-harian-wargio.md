# Wargio — Pembagian Todo List Per Hari

Dokumen ini adalah checklist eksekusi harian dari rencana hackathon Wargio.
Fokus utama: selesaikan Tier 1 lebih dulu, lalu Tier 2, baru polish.

## Aturan Eksekusi Harian

- Prioritas urutan: **stabilitas backend -> intent core -> deploy -> demo**.
- Semua write operation wajib konfirmasi user sebelum `insertOne`/`updateOne`.
- Semua angka yang dijawab agent wajib berasal dari Atlas live.
- Jika task blocker belum selesai, task nice-to-have di hari itu ditunda.
- **Git:** commit/push hanya dengan author pemilik repo — tanpa `Co-authored-by` (lihat `.cursor/rules/wargio-git.mdc`).

## Verifikasi Agentic (Wajib Setiap Task)

Setelah **satu checkbox** selesai diimplementasi, jalankan **3 fase terpisah** sebelum centang `[x]`:

```bash
python scripts/verifikasi_agentic/jalankan.py --list
python scripts/verifikasi_agentic/jalankan.py --tugas <ID> --fase verifikasi
python scripts/verifikasi_agentic/jalankan.py --tugas <ID> --fase testing
python scripts/verifikasi_agentic/jalankan.py --tugas <ID> --fase stress
# atau: npm run verifikasi:agentic -- --tugas hari3-write-intents --fase all
```

- Laporan jujur: `reports/verifikasi/*.md`
- Panduan: `agent/verifikasi/README.md`
- Cursor rule: `.cursor/rules/wargio-verifikasi-agentic.mdc`

**Jangan centang `[x]` jika verdict fase manapun = GAGAL.**

## Hari 1 — Foundation & Infra

### Target Hari Ini
- Atlas, MCP, dan FastAPI tersambung end-to-end.

### Todo
- [x] Inisialisasi git repository.
- [x] Tambah `LICENSE` (MIT) di root.
- [x] Buat `README.md` skeleton sesuai format submission.
- [x] Scaffold backend FastAPI (`/api/health`, `/api/chat`).
- [x] Tambah `.env.example` tanpa nilai rahasia.
- [x] Setup koneksi Atlas pakai `AsyncMongoClient`.
- [x] Buat collections: `products`, `transactions`, `customers`, `agent_sessions`.
- [x] Buat index dasar + vector index produk (768 dimensi) — `scripts/buat_vector_index.py`.
- [x] Seed data expanded (52 produk, 20 customer, 239 transaksi).
- [x] Setup MongoDB MCP server + verifikasi `find` (`npm run verifikasi:mcp`).

### Definition of Done
- [x] Query MCP `find` stok rendah berhasil (15 docs).
- [x] Endpoint `/api/health` return 200 + `atlas=true`.

### Catatan selesai (1 Juni + re-verifikasi 7 Juni 2026)
- [x] MCP verified — `scripts/verifikasi_mcp.mjs` (stabil: `node` langsung, tanpa EPIPE)
- [x] `0.0.0.0/0` dihapus dari Network Access
- [x] Vector index `products_vector_index` READY (768d, `name_embedding`)
- [x] Repo public & ter-push — `https://github.com/adindamochamad/wargio`
- [x] Seed minimum: 52 produk, 20 customer, 239 transaksi (gate `seed_minimum`)
- [x] README foundation: LICENSE + Live URL `https://wargio.adindamochamad.com`

### Verifikasi lokal

```bash
backend/.venv/bin/python scripts/verifikasi_hari1.py
# Agentic 3 fase:
python scripts/verifikasi_agentic/jalankan.py --tugas hari1-foundation --fase verifikasi
python scripts/verifikasi_agentic/jalankan.py --tugas hari1-foundation --fase testing
python scripts/verifikasi_agentic/jalankan.py --tugas hari1-foundation --fase stress
```

**Status Hari 1: 100% complete** (7 Juni 2026)

| Cek | Hasil |
|-----|-------|
| `verifikasi_hari1.py` | 17/17 LOLOS |
| Agentic verifikasi | LOLOS (82/100) |
| Agentic testing | LOLOS |
| Agentic stress | LOLOS |

## Hari 2 — Tier 1 Read Intents

### Target Hari Ini
- 4 intent baca berjalan dari chat API.

### Todo
- [x] Implement `check_stock`.
- [x] Implement `check_debt`.
- [x] Implement `restock_alert`.
- [x] Implement `sales_report`.
- [x] Implement session context via `X-Session-Id`.
- [x] Tambah unit test minimal 3 kasus per intent.
- [x] Tangani error MCP dengan retry 1x *(retry Atlas query 1x)*.
- [x] System prompt Wargio (`backend/app/prompts/wargio_system.txt`).
- [x] Layer MCP-equivalent tools (`atlas_tools.py`) + optional MCP live.
- [x] Integrasi Gemini agent (fallback regex jika belum dikonfigurasi).
- [x] API terima field `pesan` atau `message`.
- [x] Deploy ADK agent ke Agent Engine (`agent/wargio`, `AGENT_ENGINE_ID` di `.env`).
- [x] MCP live terverifikasi (`scripts/verifikasi_mcp.mjs` + optional pool `MCP_LIVE_ENABLED=true`) — *production: `false`, `pymongo_equivalent`*.

### Definition of Done
- [x] 4 query read intent return respons masuk akal dan konsisten dengan data Atlas.

### Verifikasi lokal

```bash
backend/.venv/bin/python scripts/verifikasi_hari2.py
# Opsional MCP live pool (lambat): backend/.venv/bin/python scripts/verifikasi_mcp_live.py
python scripts/verifikasi_agentic/jalankan.py --tugas hari2-read-intents --fase verifikasi
python scripts/verifikasi_agentic/jalankan.py --tugas hari2-read-intents --fase testing
python scripts/verifikasi_agentic/jalankan.py --tugas hari2-read-intents --fase stress
```

**Status Hari 2: 100% complete** (8 Juni 2026)

| Cek | Hasil |
|-----|-------|
| `verifikasi_hari2.py` | 11/11 LOLOS (4 intent + Gemini + MCP + Agent Engine) |
| Agentic verifikasi | LOLOS 100/100 |
| Agentic testing | LOLOS 100/100 |
| Agentic stress | LOLOS 100/100 |
| 4 read intent DoD | check_stock, check_debt, restock_alert, sales_report — data Atlas |
| Gemini | Terintegrasi; fallback regex jika quota/runtime gagal (429 free tier) |
| MCP | Standalone verified (Hari 1); production `pymongo_equivalent` by design |
| Agent Engine | `agent/wargio` + `AGENT_ENGINE_ID=7738092906182868992` |
| Production health | `agent_mode=regex` atau `gemini_with_regex_fallback`; `mcp_tools` + `judge_smoke` di `/api/health`; `mcp_live_enabled=false` |

## Hari 3 — Tier 1 Write + Tier 2 Dasar

### Target Hari Ini
- Write intents aman dan tervalidasi.

### Todo
- [x] Implement `record_sale` (cek stok -> konfirmasi -> insert transaksi -> update stok).
- [x] Implement `record_payment` (resolve customer -> konfirmasi -> update hutang -> insert transaksi).
- [x] Implement disambiguasi produk/customer ambigu.
- [x] Reject jelas untuk stok tidak cukup atau qty invalid.
- [x] Implement `debt_collection` dasar.
- [x] Implement `sales_forecast` sederhana (day-of-week average).
- [x] Tambah integration test flow `record_sale -> check_stock`.

### Definition of Done
- [x] Penjualan tercatat di `transactions`.
- [x] `stock_current` berkurang sesuai qty.
- [x] Tidak ada write tanpa konfirmasi.

### Verifikasi lokal

```bash
backend/.venv/bin/python scripts/verifikasi_hari3.py
# atau: npm run verifikasi:hari3
python scripts/verifikasi_agentic/jalankan.py --tugas hari3-write-intents --fase verifikasi
python scripts/verifikasi_agentic/jalankan.py --tugas hari3-write-intents --fase testing
python scripts/verifikasi_agentic/jalankan.py --tugas hari3-write-intents --fase stress
```

**Status Hari 3: 100% complete** (7 Juni 2026)

| Cek | Hasil |
|-----|-------|
| `verifikasi_hari3.py` | 9/9 LOLOS |
| `pytest tests/test_hari3.py` | lulus (termasuk qty negatif + stok kurang) |
| Agentic verifikasi | LOLOS |
| Agentic testing | LOLOS |
| Agentic stress | LOLOS (fix `balasan` + parse `minus N`) |
| Race stok konfirmasi | Conditional `$gte` + test `test_konfirmasi_stok_berubah_ditolak` |
| Qty 0 / nol | Pesan "Jumlah tidak valid" (bukan "format kurang jelas") |
| Fuzzy produk pipeline | `fuzzy_produk.py` — exact → partial → vector (`gemini-embedding-001`) |
| Embedding Atlas | `scripts/isi_embedding_produk.py` — 52 produk `name_embedding` |

## Hari 4 — Frontend MVP

### Target Hari Ini
- UI demo-ready untuk alur utama.

### Todo
- [x] Scaffold Next.js App Router + TypeScript strict + Tailwind.
- [x] Buat halaman chat utama.
- [x] Integrasi `POST /api/chat`.
- [x] Tambah quick actions: Cek Stok, Lihat Hutang, Laporan Hari Ini.
- [x] Tambah mini dashboard: stok kritis, ringkasan hutang, transaksi hari ini.
- [x] Mobile responsive + dark mode.
- [x] Loading state dan error state yang jelas.

### Definition of Done
- [x] Dari UI, user bisa menjalankan minimal 4 intent Tier 1 tanpa error kritis.

### Verifikasi lokal

```bash
# Terminal 1 — API
cd backend && uvicorn app.main:aplikasi --reload --port 8000

# Terminal 2 — UI (salin frontend/.env.example → frontend/.env.local)
cd frontend && npm run dev

backend/.venv/bin/python scripts/verifikasi_hari4.py
# Opsional production UI (jika deploy sudah hidup):
# export WARGIO_PUBLIC_URL=https://wargio.adindamochamad.com
python scripts/verifikasi_agentic/jalankan.py --tugas hari4-frontend --fase verifikasi
python scripts/verifikasi_agentic/jalankan.py --tugas hari4-frontend --fase testing
python scripts/verifikasi_agentic/jalankan.py --tugas hari4-frontend --fase stress
```

**Status Hari 4: 100% complete** (8 Juni 2026)

| Cek | Hasil |
|-----|-------|
| `verifikasi_hari4.py` | LOLOS (struktur + build + vitest + runtime 4 intent + CORS + UI fitur) |
| Agentic verifikasi | LOLOS 100/100 (`dashboard_route`, `frontend_ui_fitur`) |
| Agentic testing | LOLOS 100/100 (pytest health + vitest) |
| Agentic stress | LOLOS 100/100 (CORS + timeout 90s + production UI) |
| Quick actions | Cek Stok, Lihat Hutang, Laporan Hari Ini, Restock |
| Dashboard mini | `/api/dashboard` — stok kritis, hutang, transaksi hari ini |
| Dark mode + mobile | `tema-provider` + `max-w-6xl` + kelas `dark:` |
| Production | `https://wargio.adindamochamad.com/` 200 + 4 intent via same-origin `/api` |

### Mitigasi risiko (Hari 4)
- [x] Parsing error FastAPI `detail` array di `api.ts`
- [x] Banner API mati + pesan restart backend
- [x] Tema tanpa flash (inline script + provider)
- [x] Timeout chat 90s + pesan MCP lambat
- [x] `MCP_LIVE_ENABLED=false` default di `.env.example`
- [x] `verifikasi_hari4` uji runtime + vitest frontend

## Hari 5 — Deploy & Production Validation (VPS)

### Target Hari Ini
- Aplikasi live HTTPS di VPS dan bisa diuji judge.

### Todo
- [x] Artifact deploy VPS (Docker, Nginx, `docs/deploy-vps.md`).
- [x] Rate limiting per sesi (`MiddlewareRateLimit`).
- [x] Template `deploy/.env.production.example` (tanpa rahasia di git).
- [x] Smoke test `scripts/smoke_production.sh` (+ 4 intent Tier 1 + atlas check).
- [x] Verifikasi `scripts/verifikasi_hari5.py`.
- [x] Skrip orkestrator Hari 5 (`selesaikan_hari5.sh`, `siapkan_env_production.sh`, `deploy_ssh.sh`, `pasang_nginx_vps.sh`, `cek_ip_vps_atlas.sh`, `jalankan_k6_production.sh`).
- [x] Deploy di VPS Anda (`scripts/deploy_vps.sh` atau `deploy_ssh.sh`).
- [x] Nginx + SSL (Let's Encrypt) — `pasang_nginx_vps.sh`.
- [x] Atlas Network Access: allowlist IP VPS — `cek_ip_vps_atlas.sh` (IP `45.76.156.99/32`, `atlas=true`).
- [x] Isi Live URL di README (`https://wargio.adindamochamad.com`).
- [x] Live URL Devpost siap — `docs/devpost-submission.md` (field **Project URL**); paste ke form saat login Devpost.
- [x] Smoke production: `WARGIO_PRODUCTION_URL=... bash scripts/smoke_production.sh`.
- [x] (Opsional) k6 10 user — `bash scripts/jalankan_k6_production.sh` → `docs/hari5-load-test.md`.

### Definition of Done
- [x] URL production HTTPS bisa diakses incognito (`/api/health` 200, `atlas=true`).
- [x] UI + 4 intent Tier 1 jalan di domain production.
- [x] p95 response time < 5 detik untuk 10 concurrent users (uji awal, opsional) — **p95 2.84s** (lihat `docs/hari5-load-test.md`).

### Catatan selesai (7 Juni 2026)
- Frontend port host **3010** (bentrok `:3000` dengan hermes-gateway).
- Atlas allowlist VPS `45.76.156.99/32`.

### Verifikasi

```bash
export WARGIO_PRODUCTION_URL=https://wargio.adindamochamad.com
backend/.venv/bin/python scripts/verifikasi_hari5.py
bash scripts/smoke_production.sh
python scripts/verifikasi_agentic/jalankan.py --tugas hari5-deploy --fase verifikasi
python scripts/verifikasi_agentic/jalankan.py --tugas hari5-deploy --fase testing
python scripts/verifikasi_agentic/jalankan.py --tugas hari5-deploy --fase stress
```

**Status Hari 5: 100% complete** (8 Juni 2026)

| Cek | Hasil |
|-----|-------|
| `verifikasi_hari5.py` | LOLOS (artifact + docker/nginx + rate limit + HTTPS + smoke + k6 doc) |
| Agentic verifikasi | LOLOS 100/100 (`artifact_docker`, `nginx_template`, `readme_live_url_demo`, `k6_dokumentasi`) |
| Agentic testing | LOLOS 100/100 (`tests/test_health.py`) |
| Agentic stress | LOLOS 100/100 (health + smoke 4 intent + UI + k6 p95 2.84s) |
| Production HTTPS | `https://wargio.adindamochamad.com` — health `atlas=true` |
| Load test | 10 VU, p95 **2.84s** < 5s (`docs/hari5-load-test.md`) |
| Devpost Live URL | Siap di `docs/devpost-submission.md` — submit form lengkap **Hari 8** |

## Hari 6 — Testing Blitz & Hardening

### Target Hari Ini
- Turunkan risiko demo gagal.

### Todo
- [x] Jalankan unit/integration/e2e test.
- [x] Kejar coverage backend >= 80%.
- [x] Jalankan k6 untuk skenario 10 concurrent users.
- [x] Uji edge case: input kosong, qty 0/negatif, nama ambigu, MCP timeout.
- [x] Uji isolasi sesi 2 tab berbeda.
- [x] Rapikan error message agar natural Bahasa Indonesia.

### Definition of Done
- [x] Tidak ada bug kritis terbuka.
- [x] Hasil test dan load test terdokumentasi.

### Verifikasi

```bash
backend/.venv/bin/python scripts/verifikasi_hari6.py
python scripts/verifikasi_agentic/jalankan.py --tugas hari6-hardening --fase verifikasi
python scripts/verifikasi_agentic/jalankan.py --tugas hari6-hardening --fase testing
python scripts/verifikasi_agentic/jalankan.py --tugas hari6-hardening --fase stress
```

**Status Hari 6: 100% complete (jujur)** (9 Juni 2026)

| Cek | Hasil |
|-----|-------|
| `verifikasi_hari6.py` | pytest+coverage single run + vitest coverage + docs |
| Agentic verifikasi | LOLOS **100/100** |
| Agentic testing | LOLOS **100/100** (coverage backend 83%) |
| Agentic stress | LOLOS **100/100** (`mcp_fallback_pesan` = unit executor + chat) |
| pytest | **108 passed**, 0 failed |
| Coverage backend | **83%** full repo (tanpa omit) |
| Coverage frontend | **95%** `src/lib/**` |
| vitest | **14 passed** |
| k6 | p95 **2.84s** — `docs/hari5-load-test.md` |
| Bug fix | `test_check_stock_produk_kritis_status` — query nama lengkap Aqua 600ml |

## Hari 7 — Produksi Demo Video

> **Panduan lengkap:** [`docs/hari7-demo-video.md`](./hari7-demo-video.md) — Gamma prompt, ElevenLabs VO, screen record, CapCut.

### Target Hari Ini
- Video final siap upload.

### Todo
- [x] Jalankan `bash scripts/rehearsal_demo_video.sh` sebelum rekam (LOLOS production 9 Juni 2026).
- [ ] Rekam demo 3 menit sesuai script.
- [ ] Pastikan ada scene Atlas dashboard terlihat.
- [ ] Tampilkan 4 skenario utama: stock, sale, debt, sales insight.
- [ ] Tambah subtitle Bahasa Inggris.
- [ ] Upload YouTube (unlisted/public) dan verifikasi link.

### Definition of Done
- [ ] Video 1080p, durasi <= 3 menit, alur mulus tanpa error demo.

## Hari 8 sampai Deadline — Final Polish & Submit

### Target
- Submission aman, lengkap, dan tepat waktu.

### Todo
- [x] Final audit checklist teknis (`bash scripts/judge_verify.sh` — 8 intent + write + EN).
- [x] Dokumen Devpost siap salin (`docs/devpost-submission.md`).
- [x] CI GitHub Actions (pytest + vitest, `.github/workflows/ci.yml`).
- [x] README judge path + arsitektur + `npm run judge:verify`.
- [ ] Pastikan repo public (cek GitHub settings).
- [ ] Verifikasi MIT license terdeteksi di GitHub.
- [ ] Isi form Devpost lengkap (track MongoDB, URL live, repo, **video YouTube**).
- [ ] Submit maksimal H-1 deadline (10 Juni 2026).

### Definition of Done
- [ ] Submission terkirim dan semua link dapat diakses judge.
- [ ] Video demo ≤3 menit + subtitle EN (lihat Hari 7).

## Checklist Harian Cepat (Daily Standup)

- [ ] Apa blocker terbesar hari ini?
- [ ] Task Tier 1 mana yang belum selesai?
- [ ] Ada risiko DQ (credential, mock data, tanpa MCP, video >3 menit)?
- [ ] Apakah hasil hari ini meningkatkan peluang lolos Stage 1?

