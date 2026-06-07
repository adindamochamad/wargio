# Verifikasi Agentic Wargio

Sistem **3 fase terpisah** untuk audit jujur setelah menyelesaikan task di `docs/todolist-harian-wargio.md`.

## Alur Wajib (setiap task selesai)

```
Task selesai → ① Verifikasi → ② Testing → ③ Stress → baru centang [x]
```

Jangan gabungkan fase. Jangan skip jika blocker di fase sebelumnya.

## Quick Start

```bash
# Lihat semua tugas
python scripts/verifikasi_agentic/jalankan.py --list

# Sub-tugas granular (setelah implement record_sale)
python scripts/verifikasi_agentic/jalankan.py --tugas record_sale --fase verifikasi
python scripts/verifikasi_agentic/jalankan.py --tugas record_sale --fase testing
python scripts/verifikasi_agentic/jalankan.py --tugas record_sale --fase stress

# Semua fase sekaligus
python scripts/verifikasi_agentic/jalankan.py --tugas hari3-write-intents --fase all

# Prompt untuk Cursor agent (manual audit)
python scripts/verifikasi_agentic/jalankan.py --tugas hari4-frontend --fase verifikasi --agent-prompt
```

## npm shortcuts

```bash
npm run verifikasi:agentic -- --tugas hari3-write-intents --fase all
npm run verifikasi:agentic:list
```

## Laporan

Disimpan di `reports/verifikasi/` (gitignored):

- `*_verifikasi_*.md` — DoD & struktur
- `*_testing_*.md` — pytest/vitest/coverage
- `*_stress_*.md` — edge case & k6

Setiap laporan punya **penilaian_jujur** dan skor 0–100.

## Verdict

| Verdict | Arti | Centang todolist? |
|---------|------|-------------------|
| LOLOS | Semua gate hijau | Ya |
| LOLOS_DENGAN_RESERVASI | Ada WARN, tidak ada blocker | Ya, jika WARN bukan DoD |
| GAGAL | Ada blocker | **Tidak** |

## Konfigurasi

- Manifest: `manifest_tugas.yaml`
- Prompt agent: `prompts/01_verifikasi.md`, `02_testing.md`, `03_stress.md`
- Cursor rule: `.cursor/rules/wargio-verifikasi-agentic.mdc`
- Cursor skill: `.cursor/skills/wargio-verifikasi-task/SKILL.md`

## Env

| Variable | Default | Dipakai |
|----------|---------|---------|
| `WARGIO_API_URL` | `http://127.0.0.1:8000` | stress lokal |
| `WARGIO_PRODUCTION_URL` | — | stress production |
| `MONGODB_URI` | — | pytest integration |
