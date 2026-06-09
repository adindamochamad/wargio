# Hari 6 — Testing Blitz & Hardening

| Field | Nilai |
|-------|-------|
| Waktu | 9 Juni 2026 |
| pytest backend | **108 passed**, 0 failed |
| vitest frontend | **14 passed** (lib unit) |
| Coverage backend | **83%** (full repo, tanpa omit) |
| Coverage frontend | **95%** (`src/lib/**` — unit layer) |
| Load test k6 | Lihat [hari5-load-test.md](./hari5-load-test.md) — p95 **2.84s** |

## Cakupan test

| Area | File / gate |
|------|-------------|
| Unit backend | `test_unit_coverage_hari6.py` — atlas_tools MCP fallback, mcp_klien pure fn, embed, gemini mock |
| Unit | `test_hari6.py` — format_rupiah, agent_gemini, rate limit ID |
| Integration | 8 intent, write edge cases, dashboard (httpx/ASGI) |
| Edge case | input kosong, qty negatif/nol, bon tanpa nama, stok kurang |
| Isolasi sesi | 2 session_id independen + persist Atlas |
| Rate limit | HTTP 429 wajib terpicu + pesan Bahasa Indonesia |
| Agentic stress | `edge_case_hari6`, `isolasi_sesi`, `fuzzy_capslock`, `mcp_fallback_pesan` (unit executor + chat) |
| Frontend lib | `api.test.ts`, `sesi.test.ts`, `format.test.ts` |

## Perintah verifikasi

```bash
backend/.venv/bin/python scripts/verifikasi_hari6.py
backend/.venv/bin/python scripts/verifikasi_agentic/jalankan.py --tugas hari6-hardening --fase verifikasi
backend/.venv/bin/python scripts/verifikasi_agentic/jalankan.py --tugas hari6-hardening --fase testing
backend/.venv/bin/python scripts/verifikasi_agentic/jalankan.py --tugas hari6-hardening --fase stress
```

## Bug yang diperbaiki Hari 6

- `test_check_stock_produk_kritis_status` — query disambiguasi; gunakan nama lengkap **Air Mineral Aqua 600ml**.
- Assertion longgar `"customer"` (EN) diganti ke kata kunci Bahasa Indonesia.
- `verifikasi_hari6.py` — satu run pytest+coverage (tidak duplikat).

## Catatan jujur (batas yang tersisa)

- **E2E** = integrasi httpx/ASGI + stress production chat, bukan browser Playwright.
- **Komponen React** belum di-cover vitest — UI diverifikasi agentic stress + manual; coverage frontend hanya `src/lib/`.
- **mcp_klien pool stdio** (38% baris) — live pool diuji `verifikasi_mcp.mjs` / opsional `verifikasi_mcp_live.py`; cabang pure fn + disabled pool ditest unit.

## Agentic verdict

| Fase | Skor |
|------|------|
| Verifikasi | LOLOS 100/100 |
| Testing | LOLOS 100/100 |
| Stress | LOLOS 100/100 |
