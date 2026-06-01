#!/usr/bin/env python3
"""
Verifikasi ketat Definition of Done Hari 1.
Exit code 0 = lolos semua gate yang bisa dicek; 1 = ada yang gagal.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pymongo import AsyncMongoClient

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

load_dotenv(ROOT / ".env")

URI = os.getenv("MONGODB_URI", "").strip()
DB_NAME = os.getenv("MONGODB_DATABASE", "wargio_demo")

GAGAL: list[str] = []
LOLOS: list[str] = []


def catat_gagal(pesan: str) -> None:
    GAGAL.append(pesan)
    print(f"  GAGAL: {pesan}")


def catat_lolos(pesan: str) -> None:
    LOLOS.append(pesan)
    print(f"  OK: {pesan}")


def gate_repo() -> None:
    print("\n[GATE] Struktur repo")
    wajib = [
        ROOT / "LICENSE",
        ROOT / "README.md",
        ROOT / ".gitignore",
        ROOT / ".env.example",
        BACKEND / "app" / "main.py",
        BACKEND / "requirements.txt",
    ]
    for path in wajib:
        if not path.exists():
            catat_gagal(f"File hilang: {path.relative_to(ROOT)}")
        else:
            catat_lolos(f"Ada {path.relative_to(ROOT)}")

    if (ROOT / ".env").exists():
        catat_lolos(".env ada (tidak dicek isi di log)")
    else:
        catat_gagal(".env belum dibuat — salin dari .env.example")


def gate_env() -> bool:
    print("\n[GATE] Environment")
    if not URI:
        catat_gagal("MONGODB_URI kosong")
        return False
    if "PASSWORD" in URI or "USER:" in URI:
        catat_gagal("MONGODB_URI masih placeholder")
        return False
    catat_lolos("MONGODB_URI terisi")
    return True


async def gate_atlas() -> bool:
    print("\n[GATE] Atlas — ping & query stok rendah (setara MCP find)")
    try:
        klien = AsyncMongoClient(URI, serverSelectionTimeoutMS=8000)
        db = klien[DB_NAME]
        await db.command("ping")
        catat_lolos("Ping Atlas berhasil")

        filter_stok_rendah = {
            "$expr": {"$lte": ["$stock_current", "$stock_minimum"]},
        }
        kursor = db.products.find(filter_stok_rendah)
        hasil = await kursor.to_list(length=50)
        await klien.close()

        if len(hasil) == 0:
            catat_gagal(
                "Query stok rendah return 0 dokumen — jalankan: python scripts/seed_data.py"
            )
            return False
        catat_lolos(f"Query stok rendah return {len(hasil)} produk")
        for p in hasil[:3]:
            print(f"       - {p.get('name')}: stok {p.get('stock_current')}/{p.get('stock_minimum')}")
        return True
    except Exception as e:
        catat_gagal(f"Atlas: {e}")
        return False


async def gate_health_api() -> None:
    print("\n[GATE] API /api/health → 200")
    try:
        from httpx import ASGITransport, AsyncClient

        from app.main import aplikasi

        transport = ASGITransport(app=aplikasi)
        async with AsyncClient(transport=transport, base_url="http://test") as klien:
            res = await klien.get("/api/health")
        if res.status_code != 200:
            catat_gagal(f"Status {res.status_code}, body={res.text[:200]}")
            return
        data = res.json()
        if data.get("status") != "ok":
            catat_gagal(f"status bukan ok: {data}")
            return
        catat_lolos("/api/health return 200 + status ok")
        if data.get("atlas"):
            catat_lolos("Health melaporkan atlas=true")
        elif data.get("atlas_configured"):
            catat_gagal("Atlas dikonfigurasi tapi ping gagal — cek URI/network")
        else:
            catat_lolos("Atlas belum dikonfigurasi di .env (API tetap 200)")
    except Exception as e:
        catat_gagal(f"Health API: {e}")


def gate_mcp_dokumentasi() -> None:
    print("\n[GATE] MCP Server — find stok rendah")
    import subprocess

    root = Path(__file__).resolve().parents[1]
    hasil = subprocess.run(
        ["npm", "run", "verifikasi:mcp"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if hasil.returncode != 0:
        catat_gagal(f"MCP verifikasi gagal: {hasil.stderr[:200] or hasil.stdout[:200]}")
        return
    if "OK: MCP find stok rendah berhasil" in hasil.stdout:
        catat_lolos("MCP find products stok rendah berhasil")
    else:
        catat_gagal("Output MCP tidak sesuai")


async def main() -> None:
    print("=== Verifikasi Hari 1 Wargio ===")
    gate_repo()
    atlas_siap = gate_env()
    if atlas_siap:
        await gate_atlas()
    await gate_health_api()
    gate_mcp_dokumentasi()

    print("\n=== Ringkasan ===")
    print(f"Lolos: {len(LOLOS)} | Gagal: {len(GAGAL)}")
    if GAGAL:
        print("\nBlocker — perbaiki sebelum lanjut Hari 2:")
        for g in GAGAL:
            print(f"  - {g}")
        sys.exit(1)
    print("\nSemua gate lokal lolos. Lanjut Hari 2 setelah MCP manual terverifikasi.")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
