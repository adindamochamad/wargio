# Wargio — Pembagian Todo List Per Hari

Dokumen ini adalah checklist eksekusi harian dari rencana hackathon Wargio.
Fokus utama: selesaikan Tier 1 lebih dulu, lalu Tier 2, baru polish.

## Aturan Eksekusi Harian

- Prioritas urutan: **stabilitas backend -> intent core -> deploy -> demo**.
- Semua write operation wajib konfirmasi user sebelum `insertOne`/`updateOne`.
- Semua angka yang dijawab agent wajib berasal dari Atlas live.
- Jika task blocker belum selesai, task nice-to-have di hari itu ditunda.
- **Git:** commit/push hanya dengan author pemilik repo — tanpa `Co-authored-by` (lihat `.cursor/rules/wargio-git.mdc`).

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

### Catatan partial (1 Juni) — selesai
- [x] MCP verified — `scripts/verifikasi_mcp.mjs`
- [x] `0.0.0.0/0` dihapus dari Network Access
- [x] Vector index `products_vector_index` READY (768d, `name_embedding`)
- [x] Repo public & ter-push — `https://github.com/adindamochamad/wargio`

### Verifikasi lokal

```bash
backend/.venv/bin/python scripts/verifikasi_hari1.py
```

Lolos penuh Hari 1 hanya jika semua gate hijau (termasuk Atlas + seed).

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
- [x] Deploy ADK agent ke Agent Engine (`agent/wargio`, ID di `.env`).
- [x] MCP live enabled (`MCP_LIVE_ENABLED=true`, pool stdio + verifikasi).

### Definition of Done
- [x] 4 query read intent return respons masuk akal dan konsisten dengan data Atlas.

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
```

Lolos penuh Hari 3 jika semua gate hijau (termasuk `pytest tests/test_hari3.py`).

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
# atau: npm run verifikasi:hari4
# Gate: build, vitest, runtime /api/dashboard + 4 intent + CORS
```

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
- [x] Smoke test `scripts/smoke_production.sh`.
- [x] Verifikasi `scripts/verifikasi_hari5.py`.
- [ ] Deploy di VPS Anda (`scripts/deploy_vps.sh`).
- [ ] Nginx + SSL (Let's Encrypt).
- [ ] Atlas Network Access: allowlist IP VPS.
- [ ] Isi Live URL di README & Devpost.
- [ ] Smoke production: `WARGIO_PRODUCTION_URL=... bash scripts/smoke_production.sh`.
- [ ] (Opsional) k6 10 user — catat p95 di docs.

### Definition of Done
- [ ] URL production HTTPS bisa diakses incognito (`/api/health` 200, `atlas=true`).
- [ ] UI + 4 intent Tier 1 jalan di domain production.
- [ ] p95 response time < 5 detik untuk 10 concurrent users (uji awal, opsional).

### Verifikasi

```bash
backend/.venv/bin/python scripts/verifikasi_hari5.py
# Setelah deploy:
export WARGIO_PRODUCTION_URL=https://domain-anda.com
bash scripts/smoke_production.sh
```

## Hari 6 — Testing Blitz & Hardening

### Target Hari Ini
- Turunkan risiko demo gagal.

### Todo
- [ ] Jalankan unit/integration/e2e test.
- [ ] Kejar coverage backend >= 80%.
- [ ] Jalankan k6 untuk skenario 10 concurrent users.
- [ ] Uji edge case: input kosong, qty 0/negatif, nama ambigu, MCP timeout.
- [ ] Uji isolasi sesi 2 tab berbeda.
- [ ] Rapikan error message agar natural Bahasa Indonesia.

### Definition of Done
- [ ] Tidak ada bug kritis terbuka.
- [ ] Hasil test dan load test terdokumentasi.

## Hari 7 — Produksi Demo Video

### Target Hari Ini
- Video final siap upload.

### Todo
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
- [ ] Final audit checklist teknis dan submission.
- [ ] Pastikan repo public.
- [ ] Verifikasi MIT license terdeteksi.
- [ ] Isi form Devpost lengkap (track MongoDB, URL live, repo, video).
- [ ] Submit maksimal H-1 deadline.

### Definition of Done
- [ ] Submission terkirim dan semua link dapat diakses judge.

## Checklist Harian Cepat (Daily Standup)

- [ ] Apa blocker terbesar hari ini?
- [ ] Task Tier 1 mana yang belum selesai?
- [ ] Ada risiko DQ (credential, mock data, tanpa MCP, video >3 menit)?
- [ ] Apakah hasil hari ini meningkatkan peluang lolos Stage 1?

