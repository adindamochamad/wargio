"""Resolver nama produk dari database Atlas."""

from __future__ import annotations

import re
from typing import Any, Optional

from pymongo.asynchronous.database import AsyncDatabase


async def cari_produk(
    db: AsyncDatabase,
    kata_kunci: str,
    batas: int = 3,
) -> list[dict[str, Any]]:
    """
    Cari produk by nama atau alias (partial match).
    Return max `batas` hasil, urut relevansi sederhana.
    """
    teks = kata_kunci.lower().strip()
    if not teks:
        return []

    filter_query = {
        "$or": [
            {"name": {"$regex": re.escape(teks), "$options": "i"}},
            {"name_aliases": {"$regex": re.escape(teks), "$options": "i"}},
        ]
    }
    kursor = db.products.find(filter_query).limit(batas)
    return await kursor.to_list(length=batas)


async def resolve_produk_tunggal(
    db: AsyncDatabase,
    kata_kunci: Optional[str],
) -> tuple[Optional[dict[str, Any]], list[dict[str, Any]]]:
    """
    Resolve satu produk. Jika ambigu return (None, opsi).
    """
    if not kata_kunci:
        return None, []

    hasil = await cari_produk(db, kata_kunci, batas=5)
    if len(hasil) == 1:
        return hasil[0], []
    if len(hasil) > 1:
        return None, hasil[:3]
    return None, []
