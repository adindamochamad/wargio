#!/usr/bin/env python3
"""Verifikasi Hari 4 — struktur, build, runtime API + CORS + 4 intent."""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
load_dotenv(ROOT / ".env")

GAGAL: list[str] = []
LOLOS: list[str] = []

URL_API = os.getenv("WARGIO_API_URL", "http://127.0.0.1:8000").rstrip("/")
ASAL_CORS = "http://localhost:3000"


def catat_gagal(pesan: str) -> None:
    GAGAL.append(pesan)
    print(f"  GAGAL: {pesan}")


def catat_lolos(pesan: str) -> None:
    LOLOS.append(pesan)
    print(f"  OK: {pesan}")


def gate_ui_fitur() -> None:
    print("\n[GATE] Fitur UI Hari 4")
    cek = [
        (FRONTEND / "src" / "components" / "chat" / "aksi-cepat.tsx", "Cek Stok"),
        (FRONTEND / "src" / "components" / "chat" / "aksi-cepat.tsx", "Lihat Hutang"),
        (FRONTEND / "src" / "components" / "chat" / "aksi-cepat.tsx", "Laporan Hari Ini"),
        (FRONTEND / "src" / "components" / "layout" / "header.tsx", "Gelap"),
        (FRONTEND / "src" / "components" / "chat" / "chat-wargio.tsx", "sedangKirim"),
        (FRONTEND / "src" / "components" / "chat" / "chat-wargio.tsx", "pesanError"),
        (FRONTEND / "src" / "app" / "page.tsx", "max-w-6xl"),
    ]
    for path, kata in cek:
        if not path.exists():
            catat_gagal(f"Hilang: {path.relative_to(ROOT)}")
            continue
        if kata not in path.read_text(encoding="utf-8"):
            catat_gagal(f"{path.relative_to(ROOT)} tanpa fitur '{kata}'")
        else:
            catat_lolos(f"{path.relative_to(ROOT).as_posix()} — {kata}")


def gate_struktur() -> None:
    print("\n[GATE] Struktur frontend")
    wajib = [
        FRONTEND / "package.json",
        FRONTEND / "src" / "app" / "page.tsx",
        FRONTEND / "src" / "components" / "chat" / "chat-wargio.tsx",
        FRONTEND / "src" / "components" / "dashboard" / "ringkasan-dashboard.tsx",
        FRONTEND / "src" / "lib" / "api.ts",
        FRONTEND / "src" / "components" / "layout" / "status-api.tsx",
        ROOT / "backend" / "app" / "api" / "routes" / "dashboard.py",
    ]
    for path in wajib:
        if path.exists():
            catat_lolos(path.relative_to(ROOT).as_posix())
        else:
            catat_gagal(f"Hilang: {path.relative_to(ROOT)}")


def gate_env_mcp() -> None:
    print("\n[GATE] Konfigurasi MCP untuk UI")
    if os.getenv("MCP_LIVE_ENABLED", "false").lower() in ("1", "true", "yes"):
        print(
            "  PERINGATAN: MCP_LIVE_ENABLED=true — UI lambat. "
            "Set MCP_LIVE_ENABLED=false di .env untuk demo."
        )
        catat_lolos("MCP terdeteksi aktif (peringatan dicetak)")
    else:
        catat_lolos("MCP_LIVE_ENABLED=false (respons UI cepat)")


def gate_build() -> None:
    print("\n[GATE] next build")
    if not (FRONTEND / "node_modules").exists():
        catat_gagal("frontend/node_modules belum ada — cd frontend && npm install")
        return
    hasil = subprocess.run(
        ["npm", "run", "build"],
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if hasil.returncode != 0:
        catat_gagal(f"build gagal: {hasil.stderr[-400:] or hasil.stdout[-400:]}")
        return
    catat_lolos("next build sukses")


def gate_vitest() -> None:
    print("\n[GATE] vitest frontend")
    hasil = subprocess.run(
        ["npm", "run", "test"],
        cwd=FRONTEND,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if hasil.returncode != 0:
        catat_gagal(f"vitest gagal: {hasil.stdout[-300:] or hasil.stderr[-300:]}")
        return
    catat_lolos("vitest lulus")


async def gate_production_ui() -> None:
    url = (
        os.getenv("WARGIO_PRODUCTION_URL", "").strip()
        or os.getenv("WARGIO_PUBLIC_URL", "").strip()
    ).rstrip("/")
    print(f"\n[GATE] Production UI ({url or 'tidak diset'})")
    if not url:
        catat_lolos("Production URL tidak diset — lewati (dev lokal cukup)")
        return
    try:
        import httpx
    except ImportError:
        catat_gagal("httpx tidak terpasang")
        return
    try:
        async with httpx.AsyncClient(base_url=url, timeout=90.0) as klien:
            root = await klien.get("/")
            if root.status_code != 200:
                catat_gagal(f"GET / HTTP {root.status_code}")
                return
            catat_lolos(f"Frontend production {url}/ → 200")
            d = await klien.get("/api/dashboard")
            if d.status_code != 200:
                catat_gagal(f"/api/dashboard production {d.status_code}")
                return
            catat_lolos("Production /api/dashboard 200")
    except Exception as e:
        catat_gagal(f"Production UI: {e}")


async def gate_runtime_api() -> None:
    print(f"\n[GATE] Runtime API ({URL_API})")
    try:
        import httpx
    except ImportError:
        catat_gagal("httpx tidak terpasang — pip install httpx")
        return

    try:
        async with httpx.AsyncClient(base_url=URL_API, timeout=90.0) as klien:
            # Health
            h = await klien.get("/api/health")
            if h.status_code != 200:
                catat_gagal(f"/api/health status {h.status_code}")
                return
            catat_lolos("/api/health 200")

            # Dashboard — deteksi server lama tanpa route Hari 4
            d = await klien.get("/api/dashboard")
            if d.status_code == 404:
                catat_gagal(
                    "/api/dashboard 404 — RESTART backend: "
                    "cd backend && uvicorn app.main:aplikasi --reload --port 8000"
                )
                return
            if d.status_code != 200:
                catat_gagal(f"/api/dashboard status {d.status_code}")
                return
            body = d.json()
            if "jumlah_produk_kritis" not in body:
                catat_gagal("dashboard JSON tidak valid")
                return
            catat_lolos("/api/dashboard 200 + schema valid")

            # CORS preflight
            opt = await klien.options(
                "/api/chat",
                headers={
                    "Origin": ASAL_CORS,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type,x-session-id",
                },
            )
            if opt.status_code not in (200, 204):
                catat_gagal(f"CORS preflight status {opt.status_code}")
            else:
                catat_lolos("CORS preflight OK")

            # 4 intent Tier 1
            sid = "verifikasi-hari4-runtime"
            uji = [
                ("stok indomie goreng berapa?", "check_stock"),
                ("hutang Bu Sari berapa?", "check_debt"),
                ("berapa pendapatan hari ini?", "sales_report"),
                ("produk apa yang mau habis?", "restock_alert"),
            ]
            for pesan, harapan in uji:
                r = await klien.post(
                    "/api/chat",
                    json={"pesan": pesan},
                    headers={"X-Session-Id": sid},
                )
                if r.status_code != 200:
                    catat_gagal(f"chat '{harapan}' HTTP {r.status_code}")
                    continue
                intent = r.json().get("intent")
                if intent != harapan:
                    catat_gagal(f"chat '{harapan}' intent={intent}")
                else:
                    catat_lolos(f"intent {harapan} via /api/chat")

    except httpx.ConnectError:
        catat_gagal(
            f"Tidak bisa konek ke {URL_API} — jalankan uvicorn di port 8000"
        )
    except Exception as e:
        catat_gagal(f"Runtime API: {e}")


async def main() -> None:
    print("=== Verifikasi Hari 4 Wargio ===")
    gate_struktur()
    gate_ui_fitur()
    gate_env_mcp()
    gate_build()
    gate_vitest()
    await gate_runtime_api()
    await gate_production_ui()

    print("\n=== Ringkasan ===")
    print(f"Lolos: {len(LOLOS)} | Gagal: {len(GAGAL)}")
    if GAGAL:
        for g in GAGAL:
            print(f"  - {g}")
        sys.exit(1)
    print("\nHari 4 Frontend MVP: SEMUA GATE LOLOS (termasuk runtime).")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
