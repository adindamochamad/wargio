---
name: wargio-verifikasi-task
description: Jalankan 3 fase verifikasi agentic Wargio (verifikasi, testing, stress) secara terpisah dan jujur setelah menyelesaikan task todolist. Gunakan saat user atau agent menyelesaikan checkbox di docs/todolist-harian-wargio.md, setelah implement fitur intent, deploy, atau hardening.
---

# Wargio — Verifikasi Task (3 Fase Terpisah)

## Kapan Dipakai

Setelah **satu task todolist selesai diimplementasi** — sebelum centang `[x]`.

## Workflow Wajib

### 1. Tentukan ID tugas

```bash
python scripts/verifikasi_agentic/jalankan.py --list
```

Pilih ID dari manifest (`hari3-write-intents`, `record_sale`, dll.).

### 2. Fase Verifikasi (DoD)

```bash
python scripts/verifikasi_agentic/jalankan.py --tugas <ID> --fase verifikasi
```

Baca `reports/verifikasi/<ID>_verifikasi_*.md`. Jika GAGAL → perbaiki, ulangi. Jangan lanjut fase 2.

### 3. Fase Testing

```bash
python scripts/verifikasi_agentic/jalankan.py --tugas <ID> --fase testing
```

Prasyarat: `MONGODB_URI` untuk test integration. Skip Atlas = WARN, bukan lulus.

### 4. Fase Stress

```bash
# API lokal harus hidup
bash scripts/jalankan_dev.sh
python scripts/verifikasi_agentic/jalankan.py --tugas <ID> --fase stress
```

### 5. Laporkan ke User (format wajib)

```
=== AUDIT TASK: <ID> ===
Verifikasi: <verdict> (skor/100)
Testing:    <verdict> (skor/100)
Stress:     <verdict> (skor/100)
Blocker:    <daftar atau "tidak ada">
Penilaian jujur: <1-3 kalimat kritis>
Boleh centang [x]: ya/tidak
```

## Aturan Kejujuran

- LOLOS_DENGAN_RESERVASI ≠ selesai sempurna — sebutkan WARN
- Gate DILEWATI/SKIP ≠ production-ready
- Coverage <80% = belum Hari 6 selesai (jujur)
- Jangan gabungkan 3 fase jadi satu "lulus" generik

## Prompt Manual (audit mendalam)

```bash
python scripts/verifikasi_agentic/jalankan.py --tugas <ID> --fase verifikasi --agent-prompt
```

Prompt ada di `agent/verifikasi/prompts/`.

## Referensi

- Manifest: `agent/verifikasi/manifest_tugas.yaml`
- README: `agent/verifikasi/README.md`
- Rule: `.cursor/rules/wargio-verifikasi-agentic.mdc`
