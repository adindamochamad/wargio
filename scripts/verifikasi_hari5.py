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


def _url_production() -> str:
    return (
        os.getenv("WARGIO_PRODUCTION_URL", "").strip()
        or os.getenv("WARGIO_PUBLIC_URL", "").strip()
    ).rstrip("/")


def gate_smoke_production() -> None:
    print("\n[GATE] Smoke production URL")
    url = _url_production()
    if not url:
        print(
            "  INFO: Set WARGIO_PRODUCTION_URL atau WARGIO_PUBLIC_URL untuk smoke penuh"
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


def gate_devpost_live_url() -> None:
    print("\n[GATE] Devpost — Live URL siap")
    doc = ROOT / "docs" / "devpost-submission.md"
    if not doc.exists():
        catat_gagal("docs/devpost-submission.md belum ada")
        return
    teks = doc.read_text(encoding="utf-8")
    url = "https://wargio.adindamochamad.com"
    if url not in teks or "Project URL" not in teks:
        catat_gagal("Devpost draft belum berisi Project URL production")
        return
    catat_lolos(f"Live URL Devpost siap: {url} (docs/devpost-submission.md)")


def gate_readme_live_url() -> None:
    print("\n[GATE] README Live URL ## Demo")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    bagian_demo = ""
    if "## Demo" in readme:
        bagian_demo = readme.split("## Demo", 1)[1].split("##", 1)[0]
    if "adindamochamad.com" in bagian_demo:
        catat_lolos("README ## Demo: Live URL production")
    else:
        catat_gagal("README ## Demo belum berisi Live URL production")


def gate_docker_nginx() -> None:
    print("\n[GATE] Docker + Nginx template")
    compose = (ROOT / "deploy/docker/docker-compose.yml").read_text(encoding="utf-8")
    if "3010:3000" not in compose:
        catat_gagal("docker-compose belum map web ke host :3010")
    else:
        catat_lolos("docker-compose web 3010:3000")
    nginx = ROOT / "deploy/nginx/wargio.conf.example"
    if not nginx.exists():
        catat_gagal("nginx template hilang")
        return
    teks_nginx = nginx.read_text(encoding="utf-8")
    if "127.0.0.1:3010" in teks_nginx and "location /api/" in teks_nginx:
        catat_lolos("nginx upstream :3010 + proxy /api")
    else:
        catat_gagal("nginx template tidak lengkap")


def gate_k6_dokumentasi() -> None:
    print("\n[GATE] Dokumentasi load test k6")
    doc = ROOT / "docs/hari5-load-test.md"
    skrip = ROOT / "deploy/k6/smoke_10_users.js"
    if not doc.exists() or not skrip.exists():
        catat_gagal("hari5-load-test.md atau skrip k6 hilang")
        return
    if "2.84" in doc.read_text(encoding="utf-8"):
        catat_lolos("p95 2.84s terdokumentasi (threshold <5s)")
    else:
        catat_gagal("docs/hari5-load-test.md belum mencatat hasil p95")


async def gate_https_production() -> None:
    print("\n[GATE] HTTPS production")
    url = _url_production()
    if not url:
        print("  INFO: Lewati HTTPS — URL production tidak diset")
        return
    if not url.startswith("https://"):
        catat_gagal("URL production harus HTTPS")
        return
    try:
        import httpx
    except ImportError:
        catat_gagal("httpx tidak terpasang")
        return
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as klien:
            r = await klien.get(f"{url}/api/health")
            if r.status_code != 200:
                catat_gagal(f"HTTPS health {r.status_code}")
                return
            body = r.json()
            if body.get("atlas") is not True:
                catat_gagal("Production atlas!=true — cek Atlas allowlist VPS")
                return
            catat_lolos(f"HTTPS {url}/api/health 200 + atlas=true")
    except Exception as e:
        catat_gagal(f"HTTPS production: {e}")


async def main() -> None:
    print("=== Verifikasi Hari 5 Wargio (VPS) ===")
    gate_artifact_deploy()
    gate_docker_nginx()
    gate_env_production_template()
    gate_rate_limit_unit()
    gate_k6_dokumentasi()
    await gate_lokal_api()
    await gate_https_production()
    gate_smoke_production()
    gate_devpost_live_url()
    gate_readme_live_url()

    print("\n=== Ringkasan ===")
    print(f"Lolos: {len(LOLOS)} | Gagal: {len(GAGAL)}")
    if GAGAL:
        for g in GAGAL:
            print(f"  - {g}")
        sys.exit(1)
    print(f"\nHari 5 Deploy & Production: SEMUA GATE LOLOS ({len(LOLOS)} checks).")
    sys.exit(0)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
