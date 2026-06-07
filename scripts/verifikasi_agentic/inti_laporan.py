"""Inti laporan verifikasi agentic — penilaian jujur dan kritis."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal


class StatusGate(str, Enum):
    LOLOS = "lolos"
    GAGAL = "gagal"
    PERINGATAN = "peringatan"
    DILEWATI = "dilewati"


@dataclass
class HasilGate:
    """Satu gate verifikasi/testing/stress."""

    id: str
    status: StatusGate
    pesan: str
    blocker: bool = False
    bukti: str | None = None


@dataclass
class LaporanFase:
    """Laporan satu fase (verifikasi | testing | stress)."""

    fase: Literal["verifikasi", "testing", "stress"]
    tugas_id: str
    label_tugas: str
    waktu_mulai: str
    waktu_selesai: str = ""
    gates: list[HasilGate] = field(default_factory=list)
    skor: int = 0
    verdict: Literal["LOLOS", "LOLOS_DENGAN_RESERVASI", "GAGAL"] = "GAGAL"
    penilaian_jujur: str = ""
    rekomendasi: list[str] = field(default_factory=list)

    def hitung_skor_dan_verdict(self) -> None:
        """Skor 0–100 — jujur, bukan optimis."""
        if not self.gates:
            self.skor = 0
            self.verdict = "GAGAL"
            self.penilaian_jujur = "Tidak ada gate dijalankan — status tidak valid."
            return

        bobot = {"lolos": 100, "peringatan": 55, "dilewati": 30, "gagal": 0}
        total = sum(bobot[g.status.value] for g in self.gates)
        self.skor = total // len(self.gates)

        ada_blocker = any(g.blocker and g.status == StatusGate.GAGAL for g in self.gates)
        ada_warn = any(g.status == StatusGate.PERINGATAN for g in self.gates)
        ada_gagal = any(g.status == StatusGate.GAGAL for g in self.gates)

        if ada_blocker or (ada_gagal and self.skor < 50):
            self.verdict = "GAGAL"
        elif ada_warn or ada_gagal:
            self.verdict = "LOLOS_DENGAN_RESERVASI"
        else:
            self.verdict = "LOLOS"

        self._buat_penilaian_jujur(ada_blocker, ada_warn, ada_gagal)

    def _buat_penilaian_jujur(
        self,
        ada_blocker: bool,
        ada_warn: bool,
        ada_gagal: bool,
    ) -> None:
        lolos = sum(1 for g in self.gates if g.status == StatusGate.LOLOS)
        gagal = sum(1 for g in self.gates if g.status == StatusGate.GAGAL)
        warn = sum(1 for g in self.gates if g.status == StatusGate.PERINGATAN)

        if ada_blocker:
            blocker_ids = [
                g.id for g in self.gates if g.blocker and g.status == StatusGate.GAGAL
            ]
            self.penilaian_jujur = (
                f"GAGAL KRITIS — {len(blocker_ids)} blocker: {', '.join(blocker_ids)}. "
                f"Jangan tandai task selesai di todolist. "
                f"({lolos} lolos / {warn} peringatan / {gagal} gagal dari {len(self.gates)} gate)"
            )
            return

        if self.verdict == "LOLOS":
            self.penilaian_jujur = (
                f"Semua {lolos} gate lulus tanpa peringatan. "
                "Tetap waspada: gate otomatis tidak mengganti review manual judge."
            )
            return

        detail_gagal = [g.id for g in self.gates if g.status == StatusGate.GAGAL]
        detail_warn = [g.id for g in self.gates if g.status == StatusGate.PERINGATAN]
        bagian = []
        if detail_gagal:
            bagian.append(f"gagal: {', '.join(detail_gagal)}")
        if detail_warn:
            bagian.append(f"peringatan: {', '.join(detail_warn)}")
        self.penilaian_jujur = (
            f"LOLOS DENGAN RESERVASI (skor {self.skor}/100). "
            f"{'; '.join(bagian)}. "
            "Task boleh ditandai [x] hanya jika yang gagal bukan DoD blocker."
        )


@dataclass
class LaporanTugas:
    """Gabungan 3 fase untuk satu tugas."""

    tugas_id: str
    label: str
    fase: list[LaporanFase] = field(default_factory=list)

    def verdict_keseluruhan(self) -> str:
        if not self.fase:
            return "BELUM_DIJALANKAN"
        verdicts = {f.verdict for f in self.fase}
        if "GAGAL" in verdicts:
            return "GAGAL"
        if "LOLOS_DENGAN_RESERVASI" in verdicts:
            return "LOLOS_DENGAN_RESERVASI"
        return "LOLOS"

    def skor_rata(self) -> int:
        if not self.fase:
            return 0
        return sum(f.skor for f in self.fase) // len(self.fase)


def simpan_laporan(laporan: LaporanFase | LaporanTugas, direktori: Path) -> tuple[Path, Path]:
    """Simpan JSON + Markdown ringkas."""
    direktori.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    if isinstance(laporan, LaporanFase):
        nama = f"{laporan.tugas_id}_{laporan.fase}_{stamp}"
        md = _format_md_fase(laporan)
    else:
        nama = f"{laporan.tugas_id}_lengkap_{stamp}"
        md = _format_md_tugas(laporan)

    path_json = direktori / f"{nama}.json"
    path_md = direktori / f"{nama}.md"

    def _serial(obj: Any) -> Any:
        if isinstance(obj, StatusGate):
            return obj.value
        if isinstance(obj, Enum):
            return obj.value
        return obj

    path_json.write_text(
        json.dumps(asdict(laporan), indent=2, ensure_ascii=False, default=_serial),
        encoding="utf-8",
    )
    path_md.write_text(md, encoding="utf-8")
    return path_json, path_md


def _format_md_fase(l: LaporanFase) -> str:
    baris = [
        f"# Verifikasi Agentic — {l.label_tugas}",
        "",
        f"| Field | Nilai |",
        f"|-------|-------|",
        f"| Tugas | `{l.tugas_id}` |",
        f"| Fase | **{l.fase}** |",
        f"| Verdict | **{l.verdict}** |",
        f"| Skor | {l.skor}/100 |",
        f"| Waktu | {l.waktu_mulai} → {l.waktu_selesai} |",
        "",
        "## Penilaian Jujur",
        "",
        l.penilaian_jujur,
        "",
        "## Gate",
        "",
    ]
    for g in l.gates:
        simbol = {"lolos": "✅", "gagal": "❌", "peringatan": "⚠️", "dilewati": "⏭️"}
        s = simbol.get(g.status.value, "•")
        blocker = " **[BLOCKER]**" if g.blocker else ""
        baris.append(f"- {s} `{g.id}`{blocker}: {g.pesan}")
        if g.bukti:
            baris.append(f"  - Bukti: `{g.bukti[:200]}`")

    if l.rekomendasi:
        baris.extend(["", "## Rekomendasi", ""])
        for r in l.rekomendasi:
            baris.append(f"- {r}")

    return "\n".join(baris)


def _format_md_tugas(t: LaporanTugas) -> str:
    baris = [
        f"# Laporan Lengkap — {t.label}",
        "",
        f"**Verdict keseluruhan:** {t.verdict_keseluruhan()}",
        f"**Skor rata:** {t.skor_rata()}/100",
        "",
    ]
    for f in t.fase:
        baris.extend([f"## Fase: {f.fase} ({f.verdict}, {f.skor}/100)", "", f.penilaian_jujur, ""])
    return "\n".join(baris)
