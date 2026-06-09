#!/usr/bin/env python3
"""
Isi field name_embedding (768d) untuk semua produk di Atlas.
Wajib sekali setelah seed agar langkah vector search fuzzy match aktif.

Butuh GEMINI_API_KEY atau Vertex di .env.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pymongo import AsyncMongoClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

load_dotenv(ROOT / ".env")

from app.services.embed_produk import (  # noqa: E402
    buat_embedding_teks,
    teks_untuk_embedding_produk,
)

URI = os.getenv("MONGODB_URI", "").strip()
DB_NAME = os.getenv("MONGODB_DATABASE", "wargio_demo")


async def main() -> None:
    if not URI or "PASSWORD" in URI:
        print("GAGAL: MONGODB_URI belum valid")
        sys.exit(1)

    from app.config import ambil_pengaturan

    ambil_pengaturan.cache_clear()
    if not ambil_pengaturan().gemini_terkonfigurasi:
        print("GAGAL: GEMINI_API_KEY atau GOOGLE_CLOUD_PROJECT belum dikonfigurasi")
        sys.exit(1)

    klien = AsyncMongoClient(URI, serverSelectionTimeoutMS=10000)
    db = klien[DB_NAME]
    await db.command("ping")

    produk_semua = await db.products.find({}).to_list(length=200)
    print(f"=== Isi embedding {len(produk_semua)} produk ===")

    berhasil = 0
    gagal = 0
    for doc in produk_semua:
        teks = teks_untuk_embedding_produk(
            doc.get("name", ""),
            doc.get("name_aliases"),
        )
        vektor = await buat_embedding_teks(teks)
        if not vektor:
            gagal += 1
            print(f"  GAGAL embed: {doc.get('sku')} — {doc.get('name')}")
            continue
        await db.products.update_one(
            {"_id": doc["_id"]},
            {"$set": {"name_embedding": vektor}},
        )
        berhasil += 1
        if berhasil % 10 == 0:
            print(f"  ... {berhasil} produk")

    await klien.close()
    print(f"\nOK: {berhasil} produk | Gagal: {gagal}")
    if gagal:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
