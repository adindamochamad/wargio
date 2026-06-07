"""Fase 2 — Testing (pytest + vitest + coverage jujur)."""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

from inti_laporan import HasilGate, LaporanFase, StatusGate  # noqa: E402
from manifest import muat_manifest  # noqa: E402


def _py() -> Path:
    venv = BACKEND / ".venv" / "bin" / "python"
    return venv if venv.exists() else Path(sys.executable)


def _parse_pytest_arg(arg: str) -> list[str]:
    """Parse 'tests/foo.py -k bar' jadi argv pytest."""
    bagian = arg.split()
    return bagian


def _jalankan_pytest(patterns: list[str]) -> list[HasilGate]:
    gates: list[HasilGate] = []
    if not patterns:
        gates.append(
            HasilGate(
                id="pytest",
                status=StatusGate.DILEWATI,
                pesan="Tidak ada pytest terdefinisi untuk tugas ini",
                blocker=False,
            )
        )
        return gates

    for pola in patterns:
        argv = [str(_py()), "-m", "pytest", *_parse_pytest_arg(pola), "-q", "--tb=line"]
        hasil = subprocess.run(
            argv,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=300,
        )
        gabungan = (hasil.stdout or "") + (hasil.stderr or "")
        id_gate = f"pytest_{pola.split()[0].replace('/', '_')}"
        if hasil.returncode == 0:
            gates.append(
                HasilGate(
                    id=id_gate,
                    status=StatusGate.LOLOS,
                    pesan=f"pytest lulus: {pola}",
                    bukti=gabungan[-200:],
                )
            )
        else:
            # Skip karena Atlas — jujur, bukan gagal palsu
            if "skipped" in gabungan.lower() and "MONGODB_URI" in gabungan:
                gates.append(
                    HasilGate(
                        id=id_gate,
                        status=StatusGate.PERINGATAN,
                        pesan=f"pytest skip (Atlas tidak configured): {pola} — bukan lulus sungguhan",
                        blocker=False,
                        bukti=gabungan[-300:],
                    )
                )
            else:
                gates.append(
                    HasilGate(
                        id=id_gate,
                        status=StatusGate.GAGAL,
                        pesan=f"pytest gagal: {pola}",
                        blocker=True,
                        bukti=gabungan[-500:],
                    )
                )
    return gates


def _jalankan_coverage_backend() -> HasilGate:
    """Coverage backend — jujur tentang gap vs target 80%."""
    target = muat_manifest().get("target", {}).get("coverage_backend", 80)
    argv = [
        str(_py()),
        "-m",
        "pytest",
        "tests/",
        "-q",
        "--tb=no",
        "--cov=app",
        "--cov-report=term-missing:skip-covered",
        "--cov-fail-under=0",
    ]
    hasil = subprocess.run(
        argv,
        cwd=ROOT,
        env={**dict(__import__("os").environ), "PYTHONPATH": str(BACKEND)},
        capture_output=True,
        text=True,
        timeout=600,
    )
    gabungan = (hasil.stdout or "") + (hasil.stderr or "")

    # Parse TOTAL line dari coverage report
    match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", gabungan)
    if not match:
        return HasilGate(
            id="coverage_backend",
            status=StatusGate.PERINGATAN,
            pesan="pytest-cov tidak terpasang atau tidak menghasilkan laporan — pip install pytest-cov",
            blocker=False,
            bukti=gabungan[-300:],
        )

    persen = int(match.group(1))
    if persen >= target:
        return HasilGate(
            id="coverage_backend",
            status=StatusGate.LOLOS,
            pesan=f"Coverage backend {persen}% ≥ target {target}%",
            bukti=f"TOTAL {persen}%",
        )
    return HasilGate(
        id="coverage_backend",
        status=StatusGate.PERINGATAN,
        pesan=f"Coverage backend {persen}% < target {target}% — jujur: belum Hari 6 selesai",
        blocker=False,
        bukti=gabungan[-400:],
    )


def _jalankan_vitest() -> HasilGate:
    if not (FRONTEND / "node_modules").exists():
        return HasilGate(
            id="vitest",
            status=StatusGate.GAGAL,
            pesan="frontend/node_modules belum ada — npm install dulu",
            blocker=True,
        )
    hasil = subprocess.run(
        ["npm", "run", "test"],
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        timeout=120,
    )
    gabungan = (hasil.stdout or "") + (hasil.stderr or "")
    if hasil.returncode == 0:
        return HasilGate(
            id="vitest",
            status=StatusGate.LOLOS,
            pesan="vitest frontend lulus",
            bukti=gabungan[-200:],
        )
    return HasilGate(
        id="vitest",
        status=StatusGate.GAGAL,
        pesan="vitest frontend gagal",
        blocker=True,
        bukti=gabungan[-400:],
    )


def _gate_struktur_test() -> HasilGate:
    """Penilaian jujur: test file count vs standar wargio-testing.mdc."""
    test_py = list((ROOT / "tests").glob("test_*.py"))
    jumlah = len(test_py)
    if jumlah >= 6:
        return HasilGate(
            id="struktur_test",
            status=StatusGate.LOLOS,
            pesan=f"{jumlah} file test backend — baseline ada",
        )
    return HasilGate(
        id="struktur_test",
        status=StatusGate.PERINGATAN,
        pesan=f"Hanya {jumlah} file test — standar Wargio minta unit/integration/e2e terpisah",
        blocker=False,
    )


async def jalankan_fase_testing(entri: dict[str, Any]) -> LaporanFase:
    waktu_mulai = datetime.now(timezone.utc).isoformat()
    gates: list[HasilGate] = []

    gates.extend(_jalankan_pytest(entri.get("pytest") or []))

    if entri.get("vitest"):
        gates.append(_jalankan_vitest())

    # Coverage & struktur untuk hari6 atau tugas backend berat
    hari = entri.get("hari")
    gates_tambahan = entri.get("gates_tambahan") or []
    if hari == 6 or "coverage_backend" in gates_tambahan:
        gates.append(_jalankan_coverage_backend())
        gates.append(_gate_struktur_test())

    laporan = LaporanFase(
        fase="testing",
        tugas_id=entri["_id"],
        label_tugas=entri.get("label", entri["_id"]),
        waktu_mulai=waktu_mulai,
        gates=gates,
    )
    laporan.hitung_skor_dan_verdict()
    laporan.waktu_selesai = datetime.now(timezone.utc).isoformat()

    if any(g.status == StatusGate.PERINGATAN and "skip" in g.pesan.lower() for g in gates):
        laporan.rekomendasi.append(
            "Test di-skip karena Atlas — set MONGODB_URI lalu jalankan ulang untuk bukti nyata."
        )
    if any(g.id == "coverage_backend" and g.status == StatusGate.PERINGATAN for g in gates):
        laporan.rekomendasi.append(
            "Prioritaskan intent handlers + write_handlers untuk coverage — bukan hanya klasifikasi."
        )

    return laporan
