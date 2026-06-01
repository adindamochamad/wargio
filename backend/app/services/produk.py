"""Resolver nama produk dari database Atlas."""

from __future__ import annotations

import re
from typing import Any, Optional

from pymongo.asynchronous.database import AsyncDatabase

from app.services.atlas_tools import mcp_find


async def cari_produk(
    db: AsyncDatabase,
    kata_kunci: str,
    batas: int = 3,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Cari produk by nama atau alias (partial match)."""
    teks = kata_kunci.lower().strip()
    if not teks:
        return [], []

    filter_query = {
        "$or": [
            {"name": {"$regex": re.escape(teks), "$options": "i"}},
            {"name_aliases": {"$regex": re.escape(teks), "$options": "i"}},
        ]
    }
    return await mcp_find(db, "products", filter_query, limit=batas)


async def resolve_produk_tunggal(
    db: AsyncDatabase,
    kata_kunci: Optional[str],
) -> tuple[Optional[dict[str, Any]], list[dict[str, Any]], list[str]]:
    """Resolve satu produk. Jika ambigu return (None, opsi, aksi)."""
    if not kata_kunci:
        return None, [], []

    hasil, aksi = await cari_produk(db, kata_kunci, batas=5)
    if len(hasil) == 1:
        return hasil[0], [], aksi
    if len(hasil) > 1:
        return None, hasil[:3], aksi
    return None, [], aksi
