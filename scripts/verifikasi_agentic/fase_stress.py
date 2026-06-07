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


async def _stress_qty_negatif(klien: httpx.AsyncClient) -> HasilGate:
    sid = f"stress-negatif-{uuid.uuid4().hex[:8]}"
    r = await _post_chat(klien, "jual minus 2 indomie", sid)
    if r.status_code != 200:
        return HasilGate("qty_negatif", StatusGate.GAGAL, f"HTTP {r.status_code}", blocker=True)
    teks = r.json().get("response", "").lower()
    tolak = any(k in teks for k in ("tidak valid", "invalid", "negatif", "minimum", "tolak", "gagal"))
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
    teks = r.json().get("response", "").lower()
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
    teks1 = r1.json().get("response", "")
    if "konfirmasi" not in teks1.lower() and "ya" not in teks1.lower():
        return HasilGate(
            "konfirmasi_batal",
            StatusGate.PERINGATAN,
            "Respons penjualan tidak minta konfirmasi eksplisit — review alur write",
            blocker=False,
            bukti=teks1[:200],
        )
    r2 = await _post_chat(klien, "batal", sid)
    teks2 = r2.json().get("response", "").lower()
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
    teks = r.json().get("response", "")
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
    teks = r_b.json().get("response", "").lower()
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
                elif nama == "health_production":
                    gates.append(await _stress_health_production())
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
