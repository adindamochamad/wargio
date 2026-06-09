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
FRONTEND = ROOT / "frontend"
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
        # Hari 1: LICENSE + Live URL nyata di bagian Demo (contoh deploy di bawah tidak dihitung).
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        license_ada = (ROOT / "LICENSE").exists()
        bagian_demo = ""
        if "## Demo" in readme:
            bagian_demo = readme.split("## Demo", 1)[1].split("##", 1)[0]
        url_masih_placeholder = any(
            pola in bagian_demo
            for pola in ("contohdomain", "domain-anda", "_(isi URL")
        )
        live_url_ada = "https://" in bagian_demo and not url_masih_placeholder
        ok = license_ada and live_url_ada
        return _gate(
            "repo_public",
            ok,
            "README foundation: LICENSE + Live URL production di bagian Demo",
            "README belum siap Hari 1 — cek LICENSE atau Live URL di ## Demo masih placeholder",
        )

    if nama == "seed_minimum":
        uri = os.getenv("MONGODB_URI", "").strip()
        if not uri:
            return _gate("seed_minimum", False, "", "MONGODB_URI kosong", blocker=True)
        try:
            from pymongo import MongoClient

            db_name = os.getenv("MONGODB_DATABASE", "wargio_demo")
            klien = MongoClient(uri, serverSelectionTimeoutMS=8000)
            db = klien[db_name]
            jumlah_produk = db.products.count_documents({})
            jumlah_customer = db.customers.count_documents({})
            jumlah_transaksi = db.transactions.count_documents({})
            klien.close()
            ok = jumlah_produk >= 50 and jumlah_customer >= 20 and jumlah_transaksi >= 200
            ringkasan = (
                f"{jumlah_produk} produk, {jumlah_customer} customer, "
                f"{jumlah_transaksi} transaksi"
            )
            return _gate(
                "seed_minimum",
                ok,
                f"Seed minimum terpenuhi: {ringkasan}",
                f"Seed kurang dari target Hari 1: {ringkasan} (harap 50/20/200)",
            )
        except Exception as e:
            return _gate("seed_minimum", False, "", f"Gagal cek seed: {e}", blocker=True)

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
        if not pengaturan.gemini_terkonfigurasi:
            return _gate_warn(
                "gemini_atau_regex",
                True,
                "Regex fallback — Gemini belum dikonfigurasi (valid MVP)",
                "",
            )
        return _gate_warn(
            "gemini_atau_regex",
            True,
            "Gemini terintegrasi (fallback regex jika quota/runtime gagal)",
            "",
        )

    if nama == "agent_engine_id":
        from app.config import ambil_pengaturan

        agent_py = ROOT / "agent" / "wargio" / "agent.py"
        ambil_pengaturan.cache_clear()
        pengaturan = ambil_pengaturan()
        id_ada = bool(pengaturan.agent_engine_id.strip())
        kode_ada = agent_py.exists()
        ok = id_ada and kode_ada
        return _gate(
            "agent_engine_id",
            ok,
            f"ADK agent + AGENT_ENGINE_ID terisi ({pengaturan.agent_engine_id[:8]}...)"
            if ok
            else "Agent Engine siap",
            "agent/wargio/agent.py atau AGENT_ENGINE_ID di .env belum lengkap",
        )

    if nama == "mcp_standalone":
        skrip = ROOT / "scripts" / "verifikasi_mcp.mjs"
        if not skrip.exists():
            return _gate("mcp_standalone", False, "", "scripts/verifikasi_mcp.mjs hilang")
        hasil = subprocess.run(
            ["node", str(skrip)],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=180,
        )
        return _gate(
            "mcp_standalone",
            hasil.returncode == 0,
            "MCP standalone find stok rendah berhasil",
            f"verifikasi_mcp.mjs exit {hasil.returncode}",
        )

    if nama == "artifact_docker":
        compose = ROOT / "deploy" / "docker" / "docker-compose.yml"
        dockerfile_api = ROOT / "deploy" / "docker" / "Dockerfile.api"
        dockerfile_web = ROOT / "deploy" / "docker" / "Dockerfile.frontend"
        if not all(p.exists() for p in (compose, dockerfile_api, dockerfile_web)):
            return _gate("artifact_docker", False, "", "Artifact Docker Hari 5 tidak lengkap")
        teks = compose.read_text(encoding="utf-8")
        port_web = "3010:3000" in teks
        health_api = "healthcheck" in teks
        ok = port_web and health_api
        return _gate(
            "artifact_docker",
            ok,
            "docker-compose: api healthcheck + web host :3010",
            "docker-compose kurang healthcheck atau map port 3010:3000",
        )

    if nama == "nginx_template":
        nginx = ROOT / "deploy" / "nginx" / "wargio.conf.example"
        if not nginx.exists():
            return _gate("nginx_template", False, "", "deploy/nginx/wargio.conf.example hilang")
        teks = nginx.read_text(encoding="utf-8")
        ok = (
            "3010" in teks
            and "location /api/" in teks
            and "letsencrypt" in teks
            and "proxy_read_timeout" in teks
        )
        return _gate(
            "nginx_template",
            ok,
            "Nginx template: upstream :3010, /api proxy, SSL, timeout chat",
            "Template Nginx belum lengkap untuk production VPS",
        )

    if nama == "readme_live_url_demo":
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        bagian_demo = ""
        if "## Demo" in readme:
            bagian_demo = readme.split("## Demo", 1)[1].split("##", 1)[0]
        placeholder = any(
            p in bagian_demo for p in ("contohdomain", "domain-anda", "_(isi URL")
        )
        live = "https://" in bagian_demo and "adindamochamad.com" in bagian_demo
        ok = live and not placeholder
        return _gate(
            "readme_live_url_demo",
            ok,
            "Live URL production terisi di README ## Demo",
            "README ## Demo belum punya Live URL production nyata",
        )

    if nama == "devpost_live_url_siap":
        doc = ROOT / "docs" / "devpost-submission.md"
        if not doc.exists():
            return _gate("devpost_live_url_siap", False, "", "docs/devpost-submission.md hilang")
        teks = doc.read_text(encoding="utf-8")
        url = "https://wargio.adindamochamad.com"
        ok = url in teks and "Project URL" in teks
        return _gate(
            "devpost_live_url_siap",
            ok,
            f"Live URL Devpost tercatat: {url}",
            "Draft Devpost belum berisi Project URL production",
        )

    if nama == "k6_dokumentasi":
        doc = ROOT / "docs" / "hari5-load-test.md"
        skrip = ROOT / "deploy" / "k6" / "smoke_10_users.js"
        if not doc.exists() or not skrip.exists():
            return _gate("k6_dokumentasi", False, "", "Dokumentasi atau skrip k6 Hari 5 hilang")
        teks = doc.read_text(encoding="utf-8")
        ok = "p95" in teks.lower() and "2.84" in teks
        return _gate(
            "k6_dokumentasi",
            ok,
            "docs/hari5-load-test.md mencatat p95 load test",
            "Load test k6 belum terdokumentasi dengan hasil p95",
        )

    if nama == "build_next":
        return HasilGate(
            id="build_next",
            status=StatusGate.DILEWATI,
            pesan="Dicek di verifikasi_hari4.py — tidak duplikasi",
            blocker=False,
        )

    if nama == "dashboard_route":
        route_py = BACKEND / "app" / "api" / "routes" / "dashboard.py"
        main_py = BACKEND / "app" / "main.py"
        schema_py = BACKEND / "app" / "schemas" / "dashboard.py"
        if not route_py.exists():
            return _gate("dashboard_route", False, "", "dashboard.py tidak ada")
        teks_main = main_py.read_text(encoding="utf-8")
        terdaftar = "dashboard.router" in teks_main or "dashboard import" in teks_main.replace(
            "\n", " "
        )
        schema_ada = schema_py.exists()
        ok = terdaftar and schema_ada
        return _gate(
            "dashboard_route",
            ok,
            "/api/dashboard terdaftar di main + schema ResponsDashboard",
            "Route dashboard belum terpasang di FastAPI",
        )

    if nama == "frontend_ui_fitur":
        cek = [
            (FRONTEND / "src" / "components" / "chat" / "aksi-cepat.tsx", "Cek Stok"),
            (FRONTEND / "src" / "components" / "layout" / "header.tsx", "Gelap"),
            (FRONTEND / "src" / "components" / "chat" / "chat-wargio.tsx", "sedangKirim"),
            (FRONTEND / "src" / "components" / "dashboard" / "ringkasan-dashboard.tsx", "stok_kritis"),
            (FRONTEND / "src" / "app" / "layout.tsx", "prefers-color-scheme"),
        ]
        hilang = []
        for path, kata in cek:
            if not path.exists():
                hilang.append(path.name)
                continue
            if kata not in path.read_text(encoding="utf-8"):
                hilang.append(f"{path.name} (tanpa '{kata}')")
        ok = not hilang
        return _gate(
            "frontend_ui_fitur",
            ok,
            "Quick actions, dark mode, loading/error, dashboard UI terdeteksi",
            f"Fitur UI Hari 4 kurang: {', '.join(hilang[:4])}",
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
