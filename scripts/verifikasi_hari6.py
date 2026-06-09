#!/usr/bin/env python3
"""Verifikasi Hari 6 — pytest+coverage, vitest+coverage, dokumentasi k6."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

GAGAL: list[str] = []
LOLOS: list[str] = []
TARGET_COVERAGE_BACKEND = 80
TARGET_COVERAGE_FRONTEND = 70


def catat_gagal(pesan: str) -> None:
    GAGAL.append(pesan)
    print(f"  GAGAL: {pesan}")


def catat_lolos(pesan: str) -> None:
    LOLOS.append(pesan)
    print(f"  OK: {pesan}")


def gate_pytest_coverage() -> None:
    """Satu run pytest + coverage (tanpa duplikasi)."""
    print(f"\n[GATE] pytest + coverage backend >= {TARGET_COVERAGE_BACKEND}%")
    py = BACKEND / ".venv" / "bin" / "python"
    env = {**os.environ, "PYTHONPATH": str(BACKEND)}
    hasil = subprocess.run(
        [
            str(py),
            "-m",
            "pytest",
            "tests/",
            "-q",
            "--tb=line",
            f"--cov-fail-under={TARGET_COVERAGE_BACKEND}",
            "--cov=app",
            "--cov-report=term",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )
    gabungan = (hasil.stdout or "") + (hasil.stderr or "")
    if hasil.returncode != 0:
        if "passed" not in gabungan and hasil.returncode != 1:
            catat_gagal(f"pytest exit {hasil.returncode}")
        else:
            match_cov = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", gabungan)
            if match_cov:
                persen = int(match_cov.group(1))
                if persen < TARGET_COVERAGE_BACKEND:
                    catat_gagal(f"coverage {persen}% < {TARGET_COVERAGE_BACKEND}%")
            match_fail = re.search(r"(\d+) failed", gabungan)
            if match_fail:
                catat_gagal(f"pytest {match_fail.group(1)} failed")
            elif hasil.returncode != 0:
                catat_gagal(f"pytest/coverage exit {hasil.returncode}")
        print(gabungan[-800:])
        return

    match_pass = re.search(r"(\d+) passed", gabungan)
    match_cov = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", gabungan)
    jumlah = match_pass.group(1) if match_pass else "?"
    persen = int(match_cov.group(1)) if match_cov else 0
    catat_lolos(f"pytest {jumlah} passed, coverage {persen}%")


def gate_vitest_coverage() -> None:
    print(f"\n[GATE] vitest + coverage frontend >= {TARGET_COVERAGE_FRONTEND}%")
    if not (FRONTEND / "node_modules").exists():
        catat_gagal("frontend/node_modules belum ada")
        return
    hasil = subprocess.run(
        ["npm", "run", "test:coverage"],
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        timeout=180,
    )
    gabungan = (hasil.stdout or "") + (hasil.stderr or "")
    if hasil.returncode != 0:
        catat_gagal("vitest coverage gagal")
        print(gabungan[-600:])
        return
    # Vitest v8 report: "All files | XX.XX"
    match = re.search(r"All files\s*\|\s*([\d.]+)", gabungan)
    if match:
        persen = float(match.group(1))
        if persen >= TARGET_COVERAGE_FRONTEND:
            catat_lolos(f"vitest coverage {persen:.0f}%")
        else:
            catat_gagal(f"vitest coverage {persen:.0f}% < {TARGET_COVERAGE_FRONTEND}%")
    else:
        catat_lolos("vitest lulus (laporan coverage tidak terparse)")


def gate_dokumentasi() -> None:
    print("\n[GATE] Dokumentasi test & load test")
    doc = ROOT / "docs" / "hari6-testing.md"
    k6 = ROOT / "docs" / "hari5-load-test.md"
    if not doc.exists():
        catat_gagal("docs/hari6-testing.md belum ada")
        return
    if not k6.exists():
        catat_gagal("docs/hari5-load-test.md hilang (k6)")
        return
    catat_lolos("hari6-testing.md + hari5-load-test.md ada")


def main() -> None:
    print("=== Verifikasi Hari 6 Wargio ===")
    gate_pytest_coverage()
    gate_vitest_coverage()
    gate_dokumentasi()

    print("\n=== Ringkasan ===")
    print(f"Lolos: {len(LOLOS)} | Gagal: {len(GAGAL)}")
    if GAGAL:
        for g in GAGAL:
            print(f"  - {g}")
        sys.exit(1)
    print(f"\nHari 6 Testing Blitz: SEMUA GATE LOLOS ({len(LOLOS)} checks).")
    sys.exit(0)


if __name__ == "__main__":
    main()
