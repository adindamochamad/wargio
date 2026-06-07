"""Fase 1 — Verifikasi struktural & Definition of Done (jujur, bukan self-congratulatory)."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
load_dotenv(ROOT / ".env")

from inti_laporan import HasilGate, LaporanFase, StatusGate  # noqa: E402


def _gate(id_gate: str, ok: bool, pesan_ok: str, pesan_gagal: str, *, blocker: bool = True) -> HasilGate:
    return HasilGate(
        id=id_gate,
        status=StatusGate.LOLOS if ok else StatusGate.GAGAL,
        pesan=pesan_ok if ok else pesan_gagal,
        blocker=blocker,
    )


def _gate_warn(id_gate: str, ok: bool, pesan_ok: str, pesan_gagal: str) -> HasilGate:
    return HasilGate(
        id=id_gate,
        status=StatusGate.LOLOS if ok else StatusGate.PERINGATAN,
        pesan=pesan_ok if ok else pesan_gagal,
        blocker=False,
    )


def _jalankan_script_verifikasi(script_rel: str) -> HasilGate:
    path = ROOT / script_rel
    if not path.exists():
        return HasilGate(
            id="script_verifikasi",
            status=StatusGate.GAGAL,
            pesan=f"Script verifikasi tidak ada: {script_rel}",
            blocker=True,
        )
    py = BACKEND / ".venv" / "bin" / "python"
    if not py.exists():
        py = Path(sys.executable)
    hasil = subprocess.run(
        [str(py), str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if hasil.returncode == 0:
        return HasilGate(
            id="script_verifikasi",
            status=StatusGate.LOLOS,
            pesan=f"{script_rel} exit 0",
            bukti=(hasil.stdout or "")[-300:],
        )
    gabungan = (hasil.stdout or "") + (hasil.stderr or "")
    return HasilGate(
        id="script_verifikasi",
        status=StatusGate.GAGAL,
        pesan=f"{script_rel} exit {hasil.returncode}",
        blocker=True,
        bukti=gabungan[-500:],
    )


def _cek_gate_tambahan(nama: str) -> HasilGate | None:
    """Gate struktural tambahan dari manifest."""
    if nama == "repo_public":
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        ada_placeholder = "coming Hari" in readme or "_(isi URL" in readme
        return _gate_warn(
            "repo_public",
            not ada_placeholder,
            "README tidak punya placeholder obvious",
            "README masih placeholder (URL/video) — jujur: belum siap submission",
        )

    if nama == "atlas_ping":
        uri = os.getenv("MONGODB_URI", "").strip()
        if not uri:
            return _gate("atlas_ping", False, "", "MONGODB_URI kosong — verifikasi Atlas tidak valid", blocker=True)
        return HasilGate(
            id="atlas_ping",
            status=StatusGate.DILEWATI,
            pesan="Dicek oleh script verifikasi hari — hindari duplikasi",
            blocker=False,
        )

    if nama == "modul_intent_handlers":
        path = BACKEND / "app" / "services" / "intent_handlers.py"
        return _gate("modul_intent_handlers", path.exists(), "intent_handlers.py ada", "Modul intent read hilang")

    if nama == "modul_write":
        for rel in ("write_handlers.py", "konfirmasi.py", "transaksi_atomik.py"):
            if not (BACKEND / "app" / "services" / rel).exists():
                return _gate("modul_write", False, "", f"Modul write hilang: {rel}")
        return _gate("modul_write", True, "Semua modul write ada", "")

    if nama == "konfirmasi_wajib":
        teks = (BACKEND / "app" / "services" / "write_handlers.py").read_text(encoding="utf-8")
        ada = "simpan_pending" in teks and "eksekusi_record" in teks
        return _gate(
            "konfirmasi_wajib",
            ada,
            "Alur konfirmasi write terdeteksi di kode",
            "Tidak ada pola konfirmasi — write mungkin langsung eksekusi (DQ risk)",
        )

    if nama == "gemini_atau_regex":
        from app.config import ambil_pengaturan

        ambil_pengaturan.cache_clear()
        pengaturan = ambil_pengaturan()
        if pengaturan.gemini_terkonfigurasi:
            return _gate_warn("gemini_atau_regex", True, "Gemini terkonfigurasi", "")
        return _gate_warn(
            "gemini_atau_regex",
            True,
            "Hanya regex fallback — jujur: belum Agent Builder penuh di runtime chat",
            "",
        )

    if nama == "build_next":
        return HasilGate(
            id="build_next",
            status=StatusGate.DILEWATI,
            pesan="Dicek di verifikasi_hari4.py — tidak duplikasi",
            blocker=False,
        )

    if nama == "chat_component_ada":
        path = ROOT / "frontend" / "src" / "components" / "chat" / "chat-wargio.tsx"
        return _gate("chat_component_ada", path.exists(), "chat-wargio.tsx ada", "Komponen chat hilang")

    if nama == "production_url_hidup":
        url = os.getenv("WARGIO_PRODUCTION_URL", "").strip()
        if not url:
            return HasilGate(
                id="production_url_hidup",
                status=StatusGate.GAGAL,
                pesan="WARGIO_PRODUCTION_URL belum diset — deploy belum diverifikasi",
                blocker=True,
            )
        return HasilGate(
            id="production_url_hidup",
            status=StatusGate.DILEWATI,
            pesan="Health production dicek di fase stress",
            blocker=False,
        )

    if nama == "coverage_backend":
        return HasilGate(
            id="coverage_backend",
            status=StatusGate.DILEWATI,
            pesan="Coverage dihitung di fase testing — jangan double-count",
            blocker=False,
        )

    if nama == "readme_video_link":
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        ada = "youtube.com" in readme.lower() or "youtu.be" in readme.lower()
        return _gate(
            "readme_video_link",
            ada,
            "Link YouTube terdeteksi di README",
            "Belum ada link demo video — Hari 7 belum selesai",
            blocker=True,
        )

    if nama == "readme_live_url":
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        ada_placeholder = "_(isi URL" in readme or "domain-anda" in readme
        return _gate(
            "readme_live_url",
            not ada_placeholder,
            "Live URL terisi di README",
            "README masih placeholder URL — production belum siap judge",
            blocker=True,
        )

    if nama == "license_mit":
        lic = (ROOT / "LICENSE").read_text(encoding="utf-8")
        return _gate("license_mit", "MIT" in lic, "LICENSE MIT ada", "LICENSE MIT tidak terdeteksi")

    if nama == "no_secrets_in_repo":
        berbahaya = []
        for pola in (".env", "credentials.json", "service-account"):
            for path in ROOT.rglob("*"):
                if path.is_file() and pola in path.name and not str(path).endswith(".example"):
                    if ".git" in path.parts or "node_modules" in path.parts:
                        continue
                    if path.name == ".env.example":
                        continue
                    berbahaya.append(str(path.relative_to(ROOT)))
        return _gate(
            "no_secrets_in_repo",
            len(berbahaya) == 0,
            "Tidak ada file secret obvious di tree (selain .gitignore)",
            f"File berpotensi secret: {berbahaya[:5]}",
        )

    return None


async def jalankan_fase_verifikasi(entri: dict[str, Any]) -> LaporanFase:
    """Jalankan fase verifikasi untuk satu tugas."""
    waktu_mulai = datetime.now(timezone.utc).isoformat()
    gates: list[HasilGate] = []

    script = entri.get("verifikasi_script")
    if script:
        gates.append(_jalankan_script_verifikasi(script))
    elif entri.get("_tipe") == "sub_tugas":
        gates.append(
            HasilGate(
                id="inherit_parent",
                status=StatusGate.PERINGATAN,
                pesan=f"Sub-tugas '{entri['_id']}' — jalankan juga parent '{entri.get('_parent')}' untuk DoD penuh",
                blocker=False,
            )
        )

    for nama in entri.get("gates_tambahan") or []:
        gate = _cek_gate_tambahan(nama)
        if gate:
            gates.append(gate)

    if not gates:
        gates.append(
            HasilGate(
                id="tidak_ada_gate",
                status=StatusGate.PERINGATAN,
                pesan="Tidak ada gate verifikasi terdefinisi — manifest perlu diperbarui",
                blocker=False,
            )
        )

    laporan = LaporanFase(
        fase="verifikasi",
        tugas_id=entri["_id"],
        label_tugas=entri.get("label", entri["_id"]),
        waktu_mulai=waktu_mulai,
        gates=gates,
    )
    laporan.hitung_skor_dan_verdict()
    laporan.waktu_selesai = datetime.now(timezone.utc).isoformat()

    if laporan.verdict != "LOLOS":
        laporan.rekomendasi.append(
            "Jangan centang [x] di todolist sebelum blocker verifikasi hilang."
        )
    if any(g.status == StatusGate.PERINGATAN for g in gates):
        laporan.rekomendasi.append(
            "Review manual: gate peringatan sering berarti 'technically works' tapi belum submission-ready."
        )

    return laporan
