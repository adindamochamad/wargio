#!/usr/bin/env python3
"""
Orkestrator verifikasi agentic Wargio — 3 fase terpisah.

Usage:
  python scripts/verifikasi_agentic/jalankan.py --list
  python scripts/verifikasi_agentic/jalankan.py --tugas hari3-write-intents --fase verifikasi
  python scripts/verifikasi_agentic/jalankan.py --tugas record_sale --fase testing
  python scripts/verifikasi_agentic/jalankan.py --tugas hari4-frontend --fase all
  python scripts/verifikasi_agentic/jalankan.py --tugas hari3-write-intents --fase all --agent-prompt
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

# Pastikan import modul lokal
DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR))

from fase_stress import jalankan_fase_stress  # noqa: E402
from fase_testing import jalankan_fase_testing  # noqa: E402
from fase_verifikasi import jalankan_fase_verifikasi  # noqa: E402
from inti_laporan import LaporanFase, LaporanTugas, simpan_laporan  # noqa: E402
from manifest import daftar_tugas, resolve_tugas  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PROMPTS = ROOT / "agent" / "verifikasi" / "prompts"
LAPORAN_DIR = ROOT / "reports" / "verifikasi"

FASE_MAP = {
    "verifikasi": jalankan_fase_verifikasi,
    "testing": jalankan_fase_testing,
    "stress": jalankan_fase_stress,
}


def cetak_laporan_fase(laporan: LaporanFase) -> None:
    print(f"\n{'=' * 60}")
    print(f"FASE: {laporan.fase.upper()} | {laporan.label_tugas}")
    print(f"VERDICT: {laporan.verdict} | SKOR: {laporan.skor}/100")
    print(f"{'=' * 60}")
    print(f"\nPENILAIAN JUJUR:\n{laporan.penilaian_jujur}\n")
    for g in laporan.gates:
        simbol = {"lolos": "OK", "gagal": "GAGAL", "peringatan": "WARN", "dilewati": "SKIP"}
        tag = simbol.get(g.status.value, "?")
        blk = " [BLOCKER]" if g.blocker else ""
        print(f"  [{tag}]{blk} {g.id}: {g.pesan}")
    if laporan.rekomendasi:
        print("\nREKOMENDASI:")
        for r in laporan.rekomendasi:
            print(f"  → {r}")


def cetak_prompt_agent(fase: str, tugas_id: str) -> None:
    path = PROMPTS / {"verifikasi": "01_verifikasi.md", "testing": "02_testing.md", "stress": "03_stress.md"}.get(
        fase, ""
    )
    if not path or not path.exists():
        print(f"Prompt tidak ada untuk fase {fase}")
        return
    isi = path.read_text(encoding="utf-8")
    isi = isi.replace("{{TUGAS_ID}}", tugas_id)
    print(isi)


async def jalankan(args: argparse.Namespace) -> int:
    try:
        entri = resolve_tugas(args.tugas)
    except KeyError as e:
        print(e, file=sys.stderr)
        return 2

    if args.agent_prompt:
        fases = ["verifikasi", "testing", "stress"] if args.fase == "all" else [args.fase]
        for f in fases:
            print(f"\n--- PROMPT AGENT: {f} ---\n")
            cetak_prompt_agent(f, args.tugas)
        return 0

    fases_jalankan = list(FASE_MAP.keys()) if args.fase == "all" else [args.fase]
    laporan_tugas = LaporanTugas(
        tugas_id=args.tugas,
        label=entri.get("label", args.tugas),
    )
    exit_code = 0

    for nama_fase in fases_jalankan:
        handler = FASE_MAP.get(nama_fase)
        if not handler:
            print(f"Fase tidak dikenal: {nama_fase}", file=sys.stderr)
            return 2

        print(f"\n>>> Menjalankan fase: {nama_fase} ...")
        laporan = await handler(entri)
        cetak_laporan_fase(laporan)
        laporan_tugas.fase.append(laporan)

        path_json, path_md = simpan_laporan(laporan, LAPORAN_DIR)
        print(f"\nLaporan disimpan:\n  {path_md}\n  {path_json}")

        if laporan.verdict == "GAGAL":
            exit_code = 1

    if len(fases_jalankan) > 1:
        path_json, path_md = simpan_laporan(laporan_tugas, LAPORAN_DIR)
        print(f"\n{'=' * 60}")
        print(f"VERDICT KESELURUHAN: {laporan_tugas.verdict_keseluruhan()}")
        print(f"SKOR RATA: {laporan_tugas.skor_rata()}/100")
        print(f"Laporan gabungan: {path_md}")
        print(f"{'=' * 60}")

        if args.fase == "all":
            verdict = laporan_tugas.verdict_keseluruhan()
            if verdict == "LOLOS":
                print("\n✓ Task BOLEH ditandai [x] di todolist (dengan catatan: review judge manual).")
            elif verdict == "LOLOS_DENGAN_RESERVASI":
                print("\n⚠ Task boleh [x] hanya jika yang gagal BUKAN DoD blocker — baca laporan jujur.")
            else:
                print("\n✗ JANGAN tandai [x] — perbaiki blocker dulu.")

    return exit_code


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verifikasi agentic Wargio — 3 fase terpisah, penilaian jujur.",
    )
    parser.add_argument(
        "--tugas",
        help="ID tugas dari agent/verifikasi/manifest_tugas.yaml",
    )
    parser.add_argument(
        "--fase",
        choices=["verifikasi", "testing", "stress", "all"],
        default="all",
        help="Fase tunggal atau all (default: all)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Daftar semua tugas terdaftar",
    )
    parser.add_argument(
        "--agent-prompt",
        action="store_true",
        help="Cetak prompt Cursor agent untuk fase (tanpa menjalankan gate)",
    )
    args = parser.parse_args()

    if args.list:
        print("Tugas terdaftar:\n")
        for tid, label, hari in daftar_tugas():
            h = f"Hari {hari}" if hari else "sub-tugas"
            print(f"  {tid:28} {h:12} {label}")
        print("\nContoh:")
        print("  python scripts/verifikasi_agentic/jalankan.py --tugas record_sale --fase stress")
        return

    if not args.tugas:
        parser.error("--tugas wajib (atau --list)")

    code = asyncio.run(jalankan(args))
    sys.exit(code)


if __name__ == "__main__":
    main()
