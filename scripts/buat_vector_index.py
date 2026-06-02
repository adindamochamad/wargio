#!/usr/bin/env python3
"""
Buat atau verifikasi Vector Search index produk Wargio di Atlas.

M0: maksimal satu slot FTS per cluster — jika penuh, gunakan --bebaskan-slot-sample
untuk menghapus indeks bawaan sample_mflix (bukan data Wargio).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pymongo import AsyncMongoClient
from pymongo.operations import SearchIndexModel

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

URI = os.getenv("MONGODB_URI", "").strip()
DB_NAME = os.getenv("MONGODB_DATABASE", "wargio_demo")
NAMA_INDEX = "products_vector_index"
DIMENSI = 768


def uri_valid() -> bool:
    if not URI or not URI.startswith("mongodb"):
        return False
    return not any(x in URI for x in ("USER", "PASSWORD", "<password>", "changeme"))


def definisi_index() -> SearchIndexModel:
    """Definisi index selaras scripts/products_vector_index.json."""
    return SearchIndexModel(
        definition={
            "fields": [
                {
                    "type": "vector",
                    "path": "name_embedding",
                    "numDimensions": DIMENSI,
                    "similarity": "cosine",
                },
                {"type": "filter", "path": "category"},
                {"type": "filter", "path": "name_aliases"},
            ]
        },
        name=NAMA_INDEX,
        type="vectorSearch",
    )


async def daftar_semua_indeks(klien: AsyncMongoClient) -> list[tuple[str, str, str, str]]:
    """Scan cluster: (database, collection, nama_index, status)."""
    hasil: list[tuple[str, str, str, str]] = []
    for nama_db in await klien.list_database_names():
        if nama_db in ("admin", "local"):
            continue
        db = klien[nama_db]
        for nama_koleksi in await db.list_collection_names():
            try:
                kursor = await db[nama_koleksi].list_search_indexes()
                for doc in await kursor.to_list(20):
                    hasil.append(
                        (
                            nama_db,
                            nama_koleksi,
                            str(doc.get("name", "")),
                            str(doc.get("status", "")),
                        )
                    )
            except Exception:
                continue
    return hasil


async def ambil_status_wargio(klien: AsyncMongoClient) -> dict | None:
    kursor = await klien[DB_NAME].products.list_search_indexes()
    for doc in await kursor.to_list(10):
        if doc.get("name") == NAMA_INDEX:
            return doc
    return None


async def bebaskan_slot_sample(klien: AsyncMongoClient) -> bool:
    """Hapus indeks search bawaan sample_mflix agar slot M0 tersedia."""
    try:
        await klien["sample_mflix"]["movies"].drop_search_index("default")
        print("OK: Indeks sample_mflix.movies/default dihapus (slot dibebaskan).")
        return True
    except Exception as e:
        print(f"SKIP: Tidak bisa hapus indeks sample — {e}")
        return False


async def buat_index_produk(klien: AsyncMongoClient) -> str | None:
    return await klien[DB_NAME].products.create_search_index(model=definisi_index())


async def tunggu_ready(klien: AsyncMongoClient, detik_maks: int = 120) -> bool:
    langkah = 5
    for _ in range(detik_maks // langkah):
        doc = await ambil_status_wargio(klien)
        if doc and doc.get("status") == "READY":
            return True
        await asyncio.sleep(langkah)
    return False


async def jalankan(bebaskan_sample: bool) -> int:
    if not uri_valid():
        print("GAGAL: MONGODB_URI di .env belum valid.")
        return 1

    klien = AsyncMongoClient(URI, serverSelectionTimeoutMS=15000)
    try:
        doc = await ambil_status_wargio(klien)
        if doc and doc.get("status") == "READY":
            print(f"OK: {NAMA_INDEX} sudah READY di {DB_NAME}.products")
            return 0

        if doc and doc.get("status") == "PENDING":
            print(f"Menunggu {NAMA_INDEX} menjadi READY...")
            if await tunggu_ready(klien):
                print("OK: Index READY.")
                return 0
            print("GAGAL: Index masih PENDING — cek Atlas UI.")
            return 1

        print(f"Membuat index {NAMA_INDEX}...")
        try:
            await buat_index_produk(klien)
        except Exception as e:
            pesan = str(e)
            if "maximum number of FTS indexes" not in pesan:
                print(f"GAGAL: {e}")
                return 1
            print("Cluster M0: slot indeks penuh.")
            for baris in await daftar_semua_indeks(klien):
                print(f"  - {baris[0]}.{baris[1]} → {baris[2]} ({baris[3]})")
            if bebaskan_sample:
                if await bebaskan_slot_sample(klien):
                    await buat_index_produk(klien)
                else:
                    return 1
            else:
                print(
                    "Jalankan ulang dengan --bebaskan-slot-sample "
                    "atau hapus indeks non-Wargio di Atlas UI."
                )
                return 1

        if await tunggu_ready(klien):
            print(f"OK: {NAMA_INDEX} READY ({DIMENSI}d, cosine, field name_embedding).")
            return 0
        print("GAGAL: Index tidak menjadi READY dalam batas waktu.")
        return 1
    finally:
        await klien.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Buat/verifikasi vector index Wargio.")
    parser.add_argument(
        "--bebaskan-slot-sample",
        action="store_true",
        help="Hapus indeks sample_mflix.movies/default jika slot M0 penuh.",
    )
    args = parser.parse_args()
    sys.exit(asyncio.run(jalankan(args.bebaskan_slot_sample)))


if __name__ == "__main__":
    main()
