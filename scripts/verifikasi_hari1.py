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


async def gate_vector_index() -> None:
    """Vector Search index products_vector_index harus READY (768d)."""
    print("\n[GATE] Vector Search — products_vector_index")
    if not URI:
        catat_gagal("MONGODB_URI kosong — lewati cek vector index")
        return
    try:
        klien = AsyncMongoClient(URI, serverSelectionTimeoutMS=8000)
        kursor = await klien[DB_NAME].products.list_search_indexes()
        indeks_wargio = None
        for doc in await kursor.to_list(10):
            if doc.get("name") == "products_vector_index":
                indeks_wargio = doc
                break
        await klien.close()

        if not indeks_wargio:
            catat_gagal(
                "products_vector_index belum ada — jalankan: "
                "python scripts/buat_vector_index.py --bebaskan-slot-sample"
            )
            return
        status = indeks_wargio.get("status", "")
        if status != "READY":
            catat_gagal(f"products_vector_index status={status} (tunggu READY di Atlas)")
            return
        fields = (indeks_wargio.get("latestDefinition") or {}).get("fields", [])
        dimensi = next(
            (f.get("numDimensions") for f in fields if f.get("type") == "vector"),
            None,
        )
        if dimensi != 768:
            catat_gagal(f"Vector index dimensi={dimensi}, harus 768")
            return
        catat_lolos("products_vector_index READY (768d, cosine)")
    except Exception as e:
        catat_gagal(f"Vector index: {e}")


def gate_github_public() -> None:
    """Repo ter-push ke GitHub dan bersifat public (DoD partial Hari 1)."""
    print("\n[GATE] GitHub — remote & visibility")
    import subprocess

    root = Path(__file__).resolve().parents[1]
    hasil_remote = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if hasil_remote.returncode != 0:
        catat_gagal("Remote origin belum dikonfigurasi")
        return
    catat_lolos(f"Remote origin: {hasil_remote.stdout.strip()}")

    hasil_push = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if hasil_push.returncode != 0:
        catat_gagal("Git HEAD tidak valid")
        return

    hasil_ls = subprocess.run(
        ["git", "ls-remote", "origin", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if hasil_ls.returncode != 0 or not hasil_ls.stdout.strip():
        catat_gagal("Branch belum ter-push ke origin — jalankan: git push -u origin main")
        return
    catat_lolos("Branch utama ter-push ke origin")

    hasil_gh = subprocess.run(
        ["gh", "repo", "view", "--json", "isPrivate,url"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=20,
    )
    if hasil_gh.returncode == 0 and '"isPrivate":false' in hasil_gh.stdout.replace(" ", ""):
        catat_lolos("Repo GitHub public")
    elif hasil_gh.returncode != 0:
        catat_lolos("gh CLI tidak tersedia — verifikasi public manual di GitHub")
    else:
        catat_gagal("Repo masih private — ubah ke public di GitHub Settings")


async def main() -> None:
    print("=== Verifikasi Hari 1 Wargio ===")
    gate_repo()
    atlas_siap = gate_env()
    if atlas_siap:
        await gate_atlas()
        await gate_vector_index()
    await gate_health_api()
    gate_mcp_dokumentasi()
    gate_github_public()

    print("\n=== Ringkasan ===")
    print(f"Lolos: {len(LOLOS)} | Gagal: {len(GAGAL)}")
    if GAGAL:
        print("\nBlocker — perbaiki sebelum lanjut Hari 2:")
        for g in GAGAL:
            print(f"  - {g}")
        sys.exit(1)
    print("\nHari 1 Foundation: SEMUA GATE LOLOS.")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
