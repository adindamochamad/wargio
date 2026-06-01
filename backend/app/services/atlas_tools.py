"""
Akses data Atlas via operasi setara MCP tools (find, aggregate).

Saat MCP_LIVE_ENABLED=true, query diverifikasi lewat mongodb-mcp-server live.
Data find tetap dari PyMongo karena MCP find tidak mengembalikan dokumen penuh.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from pymongo.asynchronous.database import AsyncDatabase

from app.config import ambil_pengaturan


def _convert_oid(obj: Any) -> Any:
    if isinstance(obj, dict):
        if set(obj.keys()) == {"$oid"}:
            return str(obj["$oid"])
        return {k: _convert_oid(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_oid(i) for i in obj]
    return obj


async def mcp_find(
    db: AsyncDatabase,
    collection: str,
    filter_query: dict[str, Any],
    *,
    limit: int = 10,
    sort: Optional[list[tuple[str, int]]] = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Operasi find — MCP live + PyMongo untuk data aktual.

    Returns:
        (dokumen, daftar_aksi) — aksi mencatat tool MCP yang dipanggil.
    """
    aksi = ["mcp:find"]
    pengaturan = ambil_pengaturan()

    if pengaturan.mcp_live_enabled:
        try:
            from app.services.mcp_klien import panggil_mcp_find

            ringkasan = await panggil_mcp_find(
                collection, filter_query, limit=limit
            )
            aksi.append("mcp:find:live")
            if "error" in ringkasan.lower()[:80]:
                raise RuntimeError(ringkasan[:200])
        except Exception:
            aksi.append("mcp:find:live_fallback")

    kursor = db[collection].find(filter_query)
    if sort:
        kursor = kursor.sort(sort)
    dokumen = await kursor.to_list(length=limit)
    return dokumen, aksi


async def mcp_aggregate(
    db: AsyncDatabase,
    collection: str,
    pipeline: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Aggregate — MCP live jika enabled, else PyMongo."""
    pengaturan = ambil_pengaturan()
    if pengaturan.mcp_live_enabled:
        try:
            from app.services.mcp_klien import panggil_mcp_aggregate

            hasil = await panggil_mcp_aggregate(collection, pipeline)
            return hasil, ["mcp:aggregate", "mcp:aggregate:live"]
        except Exception:
            aksi_gagal = ["mcp:aggregate", "mcp:aggregate:live_fallback"]
            kursor = await db[collection].aggregate(pipeline)
            return await kursor.to_list(length=100), aksi_gagal

    kursor = await db[collection].aggregate(pipeline)
    return await kursor.to_list(length=100), ["mcp:aggregate"]


def parse_hasil_mcp_aggregate(teks: str) -> list[dict[str, Any]]:
    """Parse JSON dari respons MCP aggregate (blok untrusted-user-data)."""
    import json

    pola = re.search(
        r"<untrusted-user-data-[^>]+>\s*(\[.*?\])\s*</untrusted-user-data",
        teks,
        re.DOTALL,
    )
    if not pola:
        return []
    try:
        data = json.loads(pola.group(1))
        return [_convert_oid(d) for d in data]
    except json.JSONDecodeError:
        return []


async def mcp_insert_one(
    db: AsyncDatabase,
    collection: str,
    dokumen: dict[str, Any],
    *,
    session: Any = None,
) -> tuple[Any, list[str]]:
    """Insert satu dokumen — MCP live + PyMongo (data aktual)."""
    aksi = ["mcp:insertOne"]
    pengaturan = ambil_pengaturan()
    # MCP live di luar transaksi atomik — hindari double-write
    if pengaturan.mcp_live_enabled and session is None:
        try:
            from app.services.mcp_klien import panggil_mcp_insert_one

            await panggil_mcp_insert_one(collection, dokumen)
            aksi.append("mcp:insertOne:live")
        except Exception:
            aksi.append("mcp:insertOne:live_fallback")

    hasil = await db[collection].insert_one(dokumen, session=session)
    return hasil.inserted_id, aksi


async def mcp_update_one(
    db: AsyncDatabase,
    collection: str,
    filter_query: dict[str, Any],
    update: dict[str, Any],
    *,
    session: Any = None,
) -> tuple[int, list[str]]:
    """Update satu dokumen — MCP live + PyMongo. Return modified_count."""
    aksi = ["mcp:updateOne"]
    pengaturan = ambil_pengaturan()
    if pengaturan.mcp_live_enabled and session is None:
        try:
            from app.services.mcp_klien import panggil_mcp_update_one

            await panggil_mcp_update_one(collection, filter_query, update)
            aksi.append("mcp:updateOne:live")
        except Exception:
            aksi.append("mcp:updateOne:live_fallback")

    hasil = await db[collection].update_one(filter_query, update, session=session)
    return hasil.modified_count, aksi


__all__ = [
    "mcp_find",
    "mcp_aggregate",
    "mcp_insert_one",
    "mcp_update_one",
    "parse_hasil_mcp_aggregate",
    "_convert_oid",
]
