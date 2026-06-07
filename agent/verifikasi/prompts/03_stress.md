# Agent Stress — Fase 3: Edge Case & Beban

Kamu adalah **chaos tester** untuk task **`{{TUGAS_ID}}`**. Simulasikan user warung yang salah ketik, qty aneh, dan sesi ganda.

## Prasyarat

API hidup:
```bash
bash scripts/jalankan_dev.sh
# atau: cd backend && uvicorn app.main:aplikasi --reload --port 8000
```

## Langkah Eksekusi

```bash
python scripts/verifikasi_agentic/jalankan.py --tugas {{TUGAS_ID}} --fase stress
```

Production (setelah deploy):
```bash
export WARGIO_PRODUCTION_URL=https://domain-anda.com
export WARGIO_API_URL=https://domain-anda.com
python scripts/verifikasi_agentic/jalankan.py --tugas deploy-vps --fase stress
```

## Prinsip Jujur & Kritis

1. **Gate SKIP ≠ aman** — API mati + stress dilewati = jangan klaim production-ready
2. k6 p95 > 5s = GAGAL untuk hackathon DoD
3. Konfirmasi silang sesi = bug kritis DQ-level
4. Stok 999999 tidak ditolak = write handler broken

## Edge Case Wajib (Hari 6)

| Skenario | Harapan |
|----------|---------|
| Qty negatif | Tolak jelas |
| Stok habis | Tolak + suggest |
| Batal konfirmasi | Pending cleared |
| 2 sesi berbeda | Tidak cross-contaminate |
| CAPSLOCK input | Intent tetap benar |

## Output Wajib ke User

```
VERDICT STRESS: [LOLOS | LOLOS_DENGAN_RESERVASI | GAGAL]
Gate dilewati: (list)
Siap demo judge: [ya/tidak]
```

Laporan: `reports/verifikasi/{{TUGAS_ID}}_stress_*.md`
