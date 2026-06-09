"""Fase 3 — Stress test & edge case (HTTP + k6 opsional)."""

from __future__ import annotations

import asyncio
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

from inti_laporan import HasilGate, LaporanFase, StatusGate  # noqa: E402

URL_API = os.getenv("WARGIO_API_URL", "http://127.0.0.1:8000").rstrip("/")
URL_PROD = os.getenv("WARGIO_PRODUCTION_URL", "").rstrip("/")
TIMEOUT = 90.0


async def _post_chat(
    klien: httpx.AsyncClient,
    pesan: str,
    session_id: str,
) -> httpx.Response:
    return await klien.post(
        "/api/chat",
        json={"pesan": pesan},
        headers={"X-Session-Id": session_id},
    )


def _ambil_balasan(respons: httpx.Response) -> str:
    """API Wargio memakai field `balasan`, bukan `response`."""
    if respons.status_code != 200:
        return ""
    data = respons.json()
    return str(data.get("balasan") or data.get("response") or "")


async def _stress_qty_negatif(klien: httpx.AsyncClient) -> HasilGate:
    sid = f"stress-negatif-{uuid.uuid4().hex[:8]}"
    r = await _post_chat(klien, "jual minus 2 indomie", sid)
    if r.status_code != 200:
        return HasilGate("qty_negatif", StatusGate.GAGAL, f"HTTP {r.status_code}", blocker=True)
    teks = _ambil_balasan(r).lower()
    tolak = any(
        k in teks
        for k in (
            "tidak valid",
            "invalid",
            "negatif",
            "minimum",
            "tolak",
            "gagal",
            "kurang jelas",
            "jumlah tidak",
        )
    )
    return HasilGate(
        "qty_negatif",
        StatusGate.LOLOS if tolak else StatusGate.GAGAL,
        "Qty negatif ditolak dengan pesan jelas" if tolak else "Qty negatif tidak ditolak — bug kritis",
        blocker=not tolak,
        bukti=teks[:200],
    )


async def _stress_stok_kurang(klien: httpx.AsyncClient) -> HasilGate:
    sid = f"stress-stok-{uuid.uuid4().hex[:8]}"
    r = await _post_chat(klien, "jual 999999 indomie goreng", sid)
    if r.status_code != 200:
        return HasilGate("stok_kurang", StatusGate.GAGAL, f"HTTP {r.status_code}", blocker=True)
    teks = _ambil_balasan(r).lower()
    tolak = any(k in teks for k in ("stok", "tidak cukup", "kurang", "habis", "maksimum"))
    return HasilGate(
        "stok_kurang",
        StatusGate.LOLOS if tolak else StatusGate.GAGAL,
        "Stok tidak cukup ditolak" if tolak else "Penjualan qty ekstrem tidak ditolak — cek write handler",
        blocker=not tolak,
        bukti=teks[:200],
    )


async def _stress_konfirmasi_batal(klien: httpx.AsyncClient) -> HasilGate:
    sid = f"stress-batal-{uuid.uuid4().hex[:8]}"
    r1 = await _post_chat(klien, "jual 1 indomie goreng", sid)
    if r1.status_code != 200:
        return HasilGate("konfirmasi_batal", StatusGate.GAGAL, "Setup penjualan gagal", blocker=True)
    teks1 = _ambil_balasan(r1)
    if "konfirmasi" not in teks1.lower() and "ya" not in teks1.lower():
        return HasilGate(
            "konfirmasi_batal",
            StatusGate.PERINGATAN,
            "Respons penjualan tidak minta konfirmasi eksplisit — review alur write",
            blocker=False,
            bukti=teks1[:200],
        )
    r2 = await _post_chat(klien, "batal", sid)
    teks2 = _ambil_balasan(r2).lower()
    ok = any(k in teks2 for k in ("batal", "dibatalkan", "tidak jadi", "oke"))
    return HasilGate(
        "konfirmasi_batal",
        StatusGate.LOLOS if ok else StatusGate.GAGAL,
        "Batal pending write berhasil" if ok else "Batal tidak diproses",
        blocker=not ok,
        bukti=teks2[:200],
    )


async def _stress_disambiguasi_customer(klien: httpx.AsyncClient) -> HasilGate:
    sid = f"stress-disamb-{uuid.uuid4().hex[:8]}"
    r = await _post_chat(klien, "hutang sari berapa?", sid)
    if r.status_code != 200:
        return HasilGate("disambiguasi_customer", StatusGate.GAGAL, f"HTTP {r.status_code}", blocker=True)
    teks = _ambil_balasan(r)
    # Bisa resolve tunggal ATAU tampilkan opsi — keduanya valid
    intent = r.json().get("intent", "")
    if intent != "check_debt":
        return HasilGate(
            "disambiguasi_customer",
            StatusGate.GAGAL,
            f"Intent salah: {intent}",
            blocker=True,
        )
    return HasilGate(
        "disambiguasi_customer",
        StatusGate.LOLOS,
        "check_debt merespons (resolve atau disambiguasi)",
        bukti=teks[:200],
    )


async def _stress_intent_salah(klien: httpx.AsyncClient) -> HasilGate:
    r = await _post_chat(klien, "stok indomie berapa?", f"stress-intent-{uuid.uuid4().hex[:8]}")
    if r.status_code != 200:
        return HasilGate("intent_salah_klasifikasi", StatusGate.GAGAL, f"HTTP {r.status_code}", blocker=True)
    intent = r.json().get("intent")
    ok = intent == "check_stock"
    return HasilGate(
        "intent_salah_klasifikasi",
        StatusGate.LOLOS if ok else StatusGate.GAGAL,
        f"Intent check_stock OK" if ok else f"Intent salah: {intent}",
        blocker=not ok,
    )


async def _stress_input_kosong(klien: httpx.AsyncClient) -> HasilGate:
    r = await klien.post(
        "/api/chat",
        json={"pesan": "   "},
        headers={"X-Session-Id": f"stress-kosong-{uuid.uuid4().hex[:8]}"},
    )
    # 422 validation atau 200 dengan pesan minta input — keduanya acceptable
    if r.status_code == 422:
        return HasilGate("input_kosong_read", StatusGate.LOLOS, "Input kosong ditolak 422")
    if r.status_code == 200:
        return HasilGate("input_kosong_read", StatusGate.LOLOS, "Input kosong ditangani 200")
    return HasilGate(
        "input_kosong_read",
        StatusGate.GAGAL,
        f"Input kosong HTTP {r.status_code}",
        blocker=True,
    )


async def _stress_isolasi_sesi(klien: httpx.AsyncClient) -> HasilGate:
    sid_a = f"stress-a-{uuid.uuid4().hex[:8]}"
    sid_b = f"stress-b-{uuid.uuid4().hex[:8]}"
    await _post_chat(klien, "jual 1 indomie goreng", sid_a)
    r_b = await _post_chat(klien, "ya", sid_b)
    teks = _ambil_balasan(r_b).lower()
    # Sesi B tidak boleh mengeksekusi pending dari sesi A
    eksekusi_silang = "berhasil" in teks and "catat" in teks
    return HasilGate(
        "isolasi_sesi",
        StatusGate.LOLOS if not eksekusi_silang else StatusGate.GAGAL,
        "Sesi terisolasi — konfirmasi silang tidak terjadi"
        if not eksekusi_silang
        else "BUG: konfirmasi sesi B mengeksekusi pending sesi A",
        blocker=eksekusi_silang,
        bukti=teks[:200],
    )


async def _stress_fuzzy_capslock(klien: httpx.AsyncClient) -> HasilGate:
    r = await _post_chat(klien, "STOK INDOMIE GORENG BERAPA?", f"stress-cap-{uuid.uuid4().hex[:8]}")
    intent = r.json().get("intent") if r.status_code == 200 else None
    ok = intent == "check_stock"
    return HasilGate(
        "fuzzy_capslock",
        StatusGate.LOLOS if ok else StatusGate.GAGAL,
        "CAPSLOCK tetap check_stock" if ok else f"CAPSLOCK gagal intent={intent}",
        blocker=not ok,
    )


async def _stress_chat_timeout_ui(klien: httpx.AsyncClient) -> HasilGate:
    """Pastikan timeout UI 90s ada di kode + chat selesai dalam batas waktu."""
    import time

    api_ts = ROOT / "frontend" / "src" / "lib" / "api.ts"
    if not api_ts.exists():
        return HasilGate(
            "chat_timeout_ui",
            StatusGate.GAGAL,
            "frontend/src/lib/api.ts tidak ada",
            blocker=True,
        )
    teks_api = api_ts.read_text(encoding="utf-8")
    timeout_kode = "90_000" in teks_api or "90000" in teks_api
    if not timeout_kode:
        return HasilGate(
            "chat_timeout_ui",
            StatusGate.GAGAL,
            "BATAS_WAKTU_MS 90s tidak ditemukan di api.ts",
            blocker=True,
        )

    sid = f"stress-timeout-{uuid.uuid4().hex[:8]}"
    mulai = time.monotonic()
    r = await _post_chat(klien, "stok indomie goreng berapa?", sid)
    durasi = time.monotonic() - mulai
    if r.status_code != 200:
        return HasilGate(
            "chat_timeout_ui",
            StatusGate.GAGAL,
            f"Chat HTTP {r.status_code} — timeout UI tidak bisa diverifikasi",
            blocker=True,
        )
    ok = durasi < 90.0
    return HasilGate(
        "chat_timeout_ui",
        StatusGate.LOLOS if ok else StatusGate.GAGAL,
        f"Timeout 90s di kode + chat selesai {durasi:.1f}s"
        if ok
        else f"Chat >90s ({durasi:.1f}s) — UI terasa hang",
        blocker=not ok,
        bukti=f"durasi={durasi:.2f}s",
    )


async def _stress_production_ui() -> HasilGate:
    """Smoke production: health + dashboard + UI root + 1 intent."""
    url = URL_PROD or os.getenv("WARGIO_PUBLIC_URL", "").strip().rstrip("/")
    if not url:
        return HasilGate(
            "production_ui",
            StatusGate.PERINGATAN,
            "WARGIO_PRODUCTION_URL/WARGIO_PUBLIC_URL kosong — production UI belum diverifikasi",
            blocker=False,
        )
    try:
        async with httpx.AsyncClient(base_url=url, timeout=90.0) as klien:
            h = await klien.get("/api/health")
            if h.status_code != 200 or h.json().get("atlas") is not True:
                return HasilGate(
                    "production_ui",
                    StatusGate.GAGAL,
                    f"Production health gagal ({h.status_code})",
                    blocker=True,
                )
            d = await klien.get("/api/dashboard")
            if d.status_code != 200:
                return HasilGate(
                    "production_ui",
                    StatusGate.GAGAL,
                    f"/api/dashboard production {d.status_code}",
                    blocker=True,
                )
            root = await klien.get("/")
            if root.status_code != 200:
                return HasilGate(
                    "production_ui",
                    StatusGate.GAGAL,
                    f"Frontend / HTTP {root.status_code}",
                    blocker=True,
                )
            sid = f"stress-prod-ui-{uuid.uuid4().hex[:8]}"
            c = await klien.post(
                "/api/chat",
                json={"pesan": "stok indomie goreng berapa?"},
                headers={"X-Session-Id": sid},
            )
            if c.status_code != 200 or c.json().get("intent") != "check_stock":
                return HasilGate(
                    "production_ui",
                    StatusGate.GAGAL,
                    "Chat production check_stock gagal",
                    blocker=True,
                    bukti=(c.text or "")[:200],
                )
            return HasilGate(
                "production_ui",
                StatusGate.LOLOS,
                f"Production UI + API OK ({url})",
                bukti="health + dashboard + / + check_stock",
            )
    except httpx.HTTPError as e:
        return HasilGate(
            "production_ui",
            StatusGate.GAGAL,
            f"Tidak bisa konek production UI: {e}",
            blocker=True,
        )


async def _stress_cors(klien: httpx.AsyncClient) -> HasilGate:
    r = await klien.options(
        "/api/chat",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-session-id",
        },
    )
    ok = r.status_code in (200, 204)
    return HasilGate(
        "cors_preflight",
        StatusGate.LOLOS if ok else StatusGate.GAGAL,
        "CORS preflight OK" if ok else f"CORS status {r.status_code}",
        blocker=not ok,
    )


async def _stress_health_production() -> HasilGate:
    if not URL_PROD:
        return HasilGate(
            "health_production",
            StatusGate.PERINGATAN,
            "WARGIO_PRODUCTION_URL kosong — stress production dilewati (jujur: belum deploy)",
            blocker=False,
        )
    try:
        async with httpx.AsyncClient(base_url=URL_PROD, timeout=15.0) as klien:
            r = await klien.get("/api/health")
            if r.status_code != 200:
                return HasilGate(
                    "health_production",
                    StatusGate.GAGAL,
                    f"Production health {r.status_code}",
                    blocker=True,
                )
            body = r.json()
            atlas = body.get("atlas") is True
            return HasilGate(
                "health_production",
                StatusGate.LOLOS if atlas else StatusGate.PERINGATAN,
                "Production health 200 + atlas=true"
                if atlas
                else "Health 200 tapi atlas!=true — cek koneksi Atlas di VPS",
                blocker=not atlas,
                bukti=str(body)[:200],
            )
    except httpx.HTTPError as e:
        return HasilGate(
            "health_production",
            StatusGate.GAGAL,
            f"Tidak bisa konek production: {e}",
            blocker=True,
        )


def _stress_smoke_production_full() -> HasilGate:
    """Smoke penuh: health + atlas + dashboard + 4 intent + UI root."""
    url = URL_PROD or os.getenv("WARGIO_PUBLIC_URL", "").strip().rstrip("/")
    if not url:
        return HasilGate(
            "smoke_production_full",
            StatusGate.PERINGATAN,
            "WARGIO_PRODUCTION_URL kosong — smoke penuh dilewati",
            blocker=False,
        )
    skrip = ROOT / "scripts" / "smoke_production.sh"
    if not skrip.exists():
        return HasilGate(
            "smoke_production_full",
            StatusGate.GAGAL,
            "scripts/smoke_production.sh tidak ada",
            blocker=True,
        )
    hasil = subprocess.run(
        ["bash", str(skrip)],
        cwd=ROOT,
        env={**os.environ, "WARGIO_PRODUCTION_URL": url},
        capture_output=True,
        text=True,
        timeout=180,
    )
    gabungan = (hasil.stdout or "") + (hasil.stderr or "")
    if hasil.returncode == 0:
        return HasilGate(
            "smoke_production_full",
            StatusGate.LOLOS,
            f"Smoke production lolos: {url}",
            bukti=gabungan[-300:],
        )
    return HasilGate(
        "smoke_production_full",
        StatusGate.GAGAL,
        "Smoke production gagal — cek health/dashboard/4 intent/UI",
        blocker=True,
        bukti=gabungan[-500:],
    )


def _stress_k6_ringan() -> HasilGate:
    skrip = ROOT / "deploy" / "k6" / "smoke_10_users.js"
    if not skrip.exists():
        return HasilGate("load_k6_ringan", StatusGate.GAGAL, "Skrip k6 tidak ada", blocker=True)

    which = subprocess.run(["which", "k6"], capture_output=True)
    if which.returncode != 0:
        return HasilGate(
            "load_k6_ringan",
            StatusGate.PERINGATAN,
            "k6 tidak terpasang — install k6 untuk load test sungguhan",
            blocker=False,
        )

    base = URL_PROD or URL_API
    hasil = subprocess.run(
        ["k6", "run", "-e", f"BASE_URL={base}", str(skrip)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    gabungan = (hasil.stdout or "") + (hasil.stderr or "")
    if hasil.returncode == 0:
        return HasilGate(
            "load_k6_ringan",
            StatusGate.LOLOS,
            f"k6 10 VU lulus (BASE_URL={base})",
            bukti=gabungan[-300:],
        )
    return HasilGate(
        "load_k6_ringan",
        StatusGate.GAGAL,
        f"k6 gagal — p95 mungkin >5s atau checks <90%",
        blocker=True,
        bukti=gabungan[-500:],
    )


async def _stress_edge_case_hari6(klien: httpx.AsyncClient) -> HasilGate:
    """Bundel edge case Hari 6: kosong, qty negatif, stok tanpa produk, capslock."""
    gagal: list[str] = []

    kosong = await klien.post("/api/chat", json={"pesan": ""})
    if kosong.status_code != 422:
        gagal.append(f"pesan kosong HTTP {kosong.status_code}")

    sid = f"stress-h6-{uuid.uuid4().hex[:8]}"
    neg = await _post_chat(klien, "jual minus 1 indomie", sid)
    if neg.status_code == 200:
        teks = _ambil_balasan(neg).lower()
        if not any(k in teks for k in ("tidak valid", "negatif", "jumlah tidak", "kurang jelas")):
            gagal.append("qty negatif tidak ditolak")
    else:
        gagal.append(f"qty negatif HTTP {neg.status_code}")

    spesifik = await _post_chat(klien, "stok berapa?", f"{sid}-spesifik")
    if spesifik.status_code == 200:
        if "produk mana" not in _ambil_balasan(spesifik).lower():
            gagal.append("stok berapa? tidak minta produk")
    else:
        gagal.append(f"stok berapa HTTP {spesifik.status_code}")

    caps = await _post_chat(klien, "STOK INDOMIE GORENG BERAPA?", f"{sid}-caps")
    if caps.status_code == 200:
        if caps.json().get("intent") != "check_stock":
            gagal.append("CAPSLOCK bukan check_stock")
    else:
        gagal.append(f"CAPSLOCK HTTP {caps.status_code}")

    if gagal:
        return HasilGate(
            "edge_case_hari6",
            StatusGate.GAGAL,
            f"Edge case gagal: {', '.join(gagal)}",
            blocker=True,
            bukti="; ".join(gagal),
        )
    return HasilGate(
        "edge_case_hari6",
        StatusGate.LOLOS,
        "Edge case Hari 6: kosong, qty negatif, stok tanpa produk, CAPSLOCK",
    )


async def _stress_mcp_fallback_pesan(klien: httpx.AsyncClient) -> HasilGate:
    """Fallback error Atlas — unit test executor + chat sukses tanpa error EN."""
    import subprocess

    py = ROOT / "backend" / ".venv" / "bin" / "python"
    hasil_unit = subprocess.run(
        [
            str(py),
            "-m",
            "pytest",
            "tests/test_executor.py::test_retry_gagal_total",
            "-q",
            "--tb=line",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if hasil_unit.returncode != 0:
        return HasilGate(
            "mcp_fallback_pesan",
            StatusGate.GAGAL,
            "Unit test fallback Atlas gagal",
            blocker=True,
            bukti=(hasil_unit.stdout or "")[-300:],
        )

    sid = f"stress-mcp-{uuid.uuid4().hex[:8]}"
    r = await _post_chat(klien, "stok indomie goreng berapa?", sid)
    if r.status_code != 200:
        return HasilGate(
            "mcp_fallback_pesan",
            StatusGate.GAGAL,
            f"Chat HTTP {r.status_code}",
            blocker=True,
        )
    teks = _ambil_balasan(r).lower()
    english_kasar = ("internal server error", "traceback", "exception")
    if any(k in teks for k in english_kasar):
        return HasilGate(
            "mcp_fallback_pesan",
            StatusGate.GAGAL,
            "Balasan mengandung error Inggris mentah",
            blocker=True,
            bukti=teks[:200],
        )
    return HasilGate(
        "mcp_fallback_pesan",
        StatusGate.LOLOS,
        "Fallback Atlas ID (unit) + chat sukses tanpa error EN",
        bukti="gangguan teknis + chat OK",
    )


_STRESS_HANDLERS: dict[str, Any] = {
    "qty_negatif": _stress_qty_negatif,
    "stok_kurang": _stress_stok_kurang,
    "konfirmasi_batal": _stress_konfirmasi_batal,
    "disambiguasi_customer": _stress_disambiguasi_customer,
    "intent_salah_klasifikasi": _stress_intent_salah,
    "input_kosong_read": _stress_input_kosong,
    "isolasi_sesi": _stress_isolasi_sesi,
    "fuzzy_capslock": _stress_fuzzy_capslock,
    "cors_preflight": _stress_cors,
    "chat_timeout_ui": _stress_chat_timeout_ui,
    "edge_case_hari6": _stress_edge_case_hari6,
    "mcp_fallback_pesan": _stress_mcp_fallback_pesan,
}


async def _jalankan_stress_http(nama: str, klien: httpx.AsyncClient) -> HasilGate:
    handler = _STRESS_HANDLERS.get(nama)
    if not handler:
        return HasilGate(
            nama,
            StatusGate.DILEWATI,
            f"Stress '{nama}' belum diimplementasi",
            blocker=False,
        )
    return await handler(klien)


async def jalankan_fase_stress(entri: dict[str, Any]) -> LaporanFase:
    waktu_mulai = datetime.now(timezone.utc).isoformat()
    gates: list[HasilGate] = []
    daftar = entri.get("stress") or []

    if not daftar:
        gates.append(
            HasilGate(
                id="stress",
                status=StatusGate.DILEWATI,
                pesan="Tidak ada stress test untuk tugas ini",
                blocker=False,
            )
        )
    else:
        butuh_api = any(s in _STRESS_HANDLERS for s in daftar)
        klien_http: httpx.AsyncClient | None = None

        if butuh_api:
            try:
                klien_http = httpx.AsyncClient(base_url=URL_API, timeout=TIMEOUT)
                await klien_http.get("/api/health")
            except httpx.HTTPError:
                gates.append(
                    HasilGate(
                        id="api_hidup",
                        status=StatusGate.GAGAL,
                        pesan=f"API tidak hidup di {URL_API} — stress HTTP tidak valid",
                        blocker=True,
                    )
                )
                klien_http = None

        if klien_http:
            gates.append(
                HasilGate(
                    id="api_hidup",
                    status=StatusGate.LOLOS,
                    pesan=f"API hidup di {URL_API}",
                )
            )
            for nama in daftar:
                if nama == "load_k6_ringan":
                    gates.append(_stress_k6_ringan())
                elif nama == "smoke_production_full":
                    gates.append(_stress_smoke_production_full())
                elif nama == "health_production":
                    gates.append(await _stress_health_production())
                elif nama == "production_ui":
                    gates.append(await _stress_production_ui())
                elif nama in _STRESS_HANDLERS:
                    gates.append(await _jalankan_stress_http(nama, klien_http))
                else:
                    gates.append(
                        HasilGate(
                            nama,
                            StatusGate.DILEWATI,
                            f"Stress '{nama}' tidak dikenali",
                            blocker=False,
                        )
                    )
            await klien_http.aclose()
        else:
            for nama in daftar:
                if nama == "health_production":
                    gates.append(await _stress_health_production())
                elif nama == "smoke_production_full":
                    gates.append(_stress_smoke_production_full())
                elif nama == "production_ui":
                    gates.append(await _stress_production_ui())
                elif nama == "load_k6_ringan":
                    gates.append(_stress_k6_ringan())
                else:
                    gates.append(
                        HasilGate(
                            nama,
                            StatusGate.DILEWATI,
                            "API mati — stress HTTP dilewati",
                            blocker=False,
                        )
                    )

    laporan = LaporanFase(
        fase="stress",
        tugas_id=entri["_id"],
        label_tugas=entri.get("label", entri["_id"]),
        waktu_mulai=waktu_mulai,
        gates=gates,
    )
    laporan.hitung_skor_dan_verdict()
    laporan.waktu_selesai = datetime.now(timezone.utc).isoformat()

    if laporan.verdict == "LOLOS" and any(g.status == StatusGate.DILEWATI for g in gates):
        laporan.rekomendasi.append(
            "Stress 'lolos' tapi ada gate dilewati — jangan anggap beban production aman."
        )
    if not URL_PROD and any(s in ("health_production", "load_k6_ringan") for s in daftar):
        laporan.rekomendasi.append(
            "Set WARGIO_PRODUCTION_URL lalu ulangi stress setelah deploy VPS."
        )

    return laporan
