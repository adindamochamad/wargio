#!/usr/bin/env python3
"""
Membuat index dasar di Atlas untuk Wargio.
Vector search index 768d harus dibuat di Atlas UI (lihat docs/setup-atlas-mcp.md).
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pymongo import AsyncMongoClient, ASCENDING, DESCENDING

# Muat .env dari root repo
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

URI = os.getenv("MONGODB_URI", "").strip()
DB_NAME = os.getenv("MONGODB_DATABASE", "wargio_demo")


def uri_valid() -> bool:
    if not URI or not URI.startswith("mongodb"):
        return False
    return not any(x in URI for x in ("USER", "PASSWORD", "<password>", "changeme"))


async def buat_indeks() -> None:
    if not uri_valid():
        print("GAGAL: Edit .env — ganti MONGODB_URI placeholder dengan connection string Atlas asli.")
        print("       Atlas → Connect → Drivers → copy URI, ganti password user DB.")
        sys.exit(1)

    klien = AsyncMongoClient(URI)
    db = klien[DB_NAME]

    # products
    await db.products.create_index([("sku", ASCENDING)], unique=True)
    await db.products.create_index([("name", ASCENDING)])
    await db.products.create_index([("stock_current", ASCENDING)])
    await db.products.create_index([("category", ASCENDING)])

    # transactions
    await db.transactions.create_index([("created_at", DESCENDING)])
    await db.transactions.create_index([("type", ASCENDING), ("created_at", DESCENDING)])

    # customers
    await db.customers.create_index([("name", ASCENDING)])
    await db.customers.create_index([("debt_total", DESCENDING)])

    # agent_sessions
    await db.agent_sessions.create_index([("session_id", ASCENDING)], unique=True)

    await klien.close()
    print("OK: Index dasar berhasil dibuat.")
    print("Lanjut: python scripts/buat_vector_index.py")


if __name__ == "__main__":
    asyncio.run(buat_indeks())
