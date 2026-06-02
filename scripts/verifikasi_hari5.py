#!/usr/bin/env python3
"""Verifikasi Hari 5 — deploy VPS + smoke production opsional."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GAGAL: list[str] = []
LOLOS: list[str] = []


def catat_gagal(pesan: str) -> None:
    GAGAL.append(pesan)
    print(f"  GAGAL: {pesan}")


def catat_lolos(pesan: str) -> None:
    LOLOS.append(pesan)
    print(f"  OK: {pesan}")


def gate_artifact_deploy() -> None:
    print("\n[GATE] Artifact deploy VPS")
    wajib = [
        "docs/deploy-vps.md",
        "deploy/docker/docker-compose.yml",
        "deploy/docker/Dockerfile.api",
        "deploy/docker/Dockerfile.frontend",
        "deploy/nginx/wargio.conf.example",
        "deploy/.env.production.example",
        "scripts/smoke_production.sh",
        "backend/app/middleware/rate_limit.py",
    ]
    for rel in wajib:
        if (ROOT / rel).exists():
            catat_lolos(rel)
        else:
            catat_gagal(f"Hilang: {rel}")


def gate_env_production_template() -> None:
    print("\n[GATE] Template production tanpa rahasia")
    contoh = (ROOT / "deploy/.env.production.example").read_text()
    if "PASSWORD" in contoh and "mongodb+srv://USER" in contoh:
        catat_lolos("Placeholder aman di .env.production.example")
    if (ROOT / "deploy/.env.production").exists():
        catat_lolos("deploy/.env.production ada (lokal, jangan commit)")
    else:
        print("  INFO: Buat deploy/.env.production dari template sebelum deploy VPS")


def gate_rate_limit_unit() -> None:
    print("\n[GATE] Rate limit middleware")
    sys.path.insert(0, str(ROOT / "backend"))
    from app.middleware.rate_limit import _bersihkan_dan_hitung

    kunci = "uji"
    sekarang = 1000.0
    for _ in range(30):
        assert _bersihkan_dan_hitung(kunci, 30, sekarang)
    if _bersihkan_dan_hitung(kunci, 30, sekarang):
        catat_gagal("Rate limit seharusnya tolak permintaan ke-31")
        return
    catat_lolos("Rate limit 30/menit berfungsi")


async def gate_lokal_api() -> None:
    print("\n[GATE] API lokal (opsional, port 8000)")
    import httpx

    try:
        async with httpx.AsyncClient(
            base_url="http://127.0.0.1:8000", timeout=5.0
        ) as klien:
            r = await klien.get("/api/health")
            if r.status_code == 200:
                catat_lolos("Lokal /api/health 200")
            else:
                print("  INFO: API lokal tidak jalan — lewati")
    except Exception:
        print("  INFO: API lokal tidak jalan — lewati")


def gate_smoke_production() -> None:
    print("\n[GATE] Smoke production URL")
    url = os.getenv("WARGIO_PRODUCTION_URL", "").strip().rstrip("/")
    if not url:
        print(
            "  INFO: Set WARGIO_PRODUCTION_URL=https://domain untuk smoke penuh"
        )
        return

    hasil = subprocess.run(
        ["bash", str(ROOT / "scripts/smoke_production.sh")],
        env={**os.environ, "WARGIO_PRODUCTION_URL": url},
        capture_output=True,
        text=True,
        timeout=120,
    )
    if hasil.returncode != 0:
        catat_gagal(
            f"Smoke production gagal: {hasil.stdout[-300:] or hasil.stderr[-300:]}"
        )
        return
    catat_lolos(f"Smoke production lolos: {url}")


def gate_readme_live_url() -> None:
    print("\n[GATE] README bagian deploy")
    readme = (ROOT / "README.md").read_text()
    if "deploy-vps" in readme or "Production" in readme or "VPS" in readme:
        catat_lolos("README menyebut deploy production")
    else:
        catat_gagal("README belum ada bagian deploy — tambahkan Live URL")


async def main() -> None:
    print("=== Verifikasi Hari 5 Wargio (VPS) ===")
    gate_artifact_deploy()
    gate_env_production_template()
    gate_rate_limit_unit()
    await gate_lokal_api()
    gate_smoke_production()
    gate_readme_live_url()

    print("\n=== Ringkasan ===")
    print(f"Lolos: {len(LOLOS)} | Gagal: {len(GAGAL)}")
    if GAGAL:
        for g in GAGAL:
            print(f"  - {g}")
        sys.exit(1)
    print("\nHari 5 artifact VPS: LOLOS.")
    print("Deploy: ikuti docs/deploy-vps.md lalu smoke dengan WARGIO_PRODUCTION_URL.")
    sys.exit(0)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
