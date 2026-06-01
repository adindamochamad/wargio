"""
Klien MCP MongoDB — stdio transport ke mongodb-mcp-server.

Pool sesi dipertahankan saat MCP_LIVE_ENABLED agar tidak spawn npx tiap request.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from contextlib import AsyncExitStack
from datetime import datetime
from typing import Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.config import ambil_pengaturan


def _convert_oid(obj: Any) -> Any:
    if isinstance(obj, dict):
        if set(obj.keys()) == {"$oid"}:
            return str(obj["$oid"])
        return {k: _convert_oid(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_oid(i) for i in obj]
    return obj


def parse_hasil_mcp_aggregate(teks: str) -> list[dict[str, Any]]:
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

_TIMEOUT_MCP = 60.0

# Pool sesi MCP — hidup sepanjang proses FastAPI
_stack: Optional[AsyncExitStack] = None
_sesi: Optional[ClientSession] = None
_kunci_pool = asyncio.Lock()


def _param_mcp() -> StdioServerParameters:
    pengaturan = ambil_pengaturan()
    return StdioServerParameters(
        command="npx",
        args=["-y", "mongodb-mcp-server@latest"],
        env={
            **os.environ,
            "MDB_MCP_CONNECTION_STRING": pengaturan.mongodb_uri,
        },
    )


async def mulai_pool_mcp() -> bool:
    """Buka koneksi MCP persisten — dipanggil saat startup FastAPI."""
    global _stack, _sesi
    if not ambil_pengaturan().mcp_live_enabled:
        return False
    async with _kunci_pool:
        if _sesi is not None:
            return True
        try:
            stack = AsyncExitStack()
            read, write = await stack.enter_async_context(stdio_client(_param_mcp()))
            sesi = await stack.enter_async_context(ClientSession(read, write))
            await asyncio.wait_for(sesi.initialize(), timeout=_TIMEOUT_MCP)
            daftar = await sesi.list_tools()
            nama = {t.name for t in daftar.tools}
            if "find" not in nama or "aggregate" not in nama:
                await stack.aclose()
                return False
            # insert-one / update-one opsional — write fallback ke PyMongo
            _stack = stack
            _sesi = sesi
            return True
        except Exception:
            if _stack:
                await _stack.aclose()
            _stack = None
            _sesi = None
            return False


async def tutup_pool_mcp() -> None:
    """Tutup pool MCP saat shutdown."""
    global _stack, _sesi
    async with _kunci_pool:
        if _stack is not None:
            try:
                await _stack.aclose()
            except Exception:
                # MCP stdio sering raise BrokenResourceError saat cleanup
                pass
        _stack = None
        _sesi = None


async def cek_mcp_hidup() -> bool:
    """Ping MCP — pakai pool jika ada, else spawn sekali."""
    if _sesi is not None:
        return True
    return await mulai_pool_mcp()


async def _dapatkan_sesi() -> ClientSession:
    if _sesi is None:
        ok = await mulai_pool_mcp()
        if not ok or _sesi is None:
            raise RuntimeError("MCP pool tidak tersedia")
    return _sesi


async def panggil_mcp_find(
    collection: str,
    filter_query: dict[str, Any],
    *,
    limit: int = 10,
) -> str:
    """
    Panggil MCP find — return teks respons (metadata, bukan dokumen penuh).
  """
    sesi = await _dapatkan_sesi()
    pengaturan = ambil_pengaturan()
    hasil = await asyncio.wait_for(
        sesi.call_tool(
            "find",
            {
                "database": pengaturan.mongodb_database,
                "collection": collection,
                "filter": filter_query,
                "limit": limit,
            },
        ),
        timeout=_TIMEOUT_MCP,
    )
    if hasil.isError:
        raise RuntimeError((hasil.content[0].text if hasil.content else "MCP find error")[:200])
    return hasil.content[0].text if hasil.content else ""


async def panggil_mcp_aggregate(
    collection: str,
    pipeline: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Panggil MCP aggregate dan parse hasil JSON."""
    sesi = await _dapatkan_sesi()
    pengaturan = ambil_pengaturan()
    hasil = await asyncio.wait_for(
        sesi.call_tool(
            "aggregate",
            {
                "database": pengaturan.mongodb_database,
                "collection": collection,
                "pipeline": pipeline,
            },
        ),
        timeout=_TIMEOUT_MCP,
    )
    teks = "".join(
        getattr(c, "text", "") or "" for c in (hasil.content or [])
    )
    if hasil.isError or (
        "error" in teks.lower()[:80]
        and "documents" not in teks.lower()
        and "aggregation" not in teks.lower()
    ):
        raise RuntimeError(teks[:200])
    parsed = parse_hasil_mcp_aggregate(teks)
    if parsed:
        return parsed
    m = re.search(r"(\[\{.*\}\])", teks, re.DOTALL)
    if m:
        return [_convert_oid(d) for d in json.loads(m.group(1))]
    raise RuntimeError("MCP aggregate tidak mengembalikan data")


def _dokumen_ke_json_mcp(dokumen: dict[str, Any]) -> dict[str, Any]:
    """Konversi ObjectId ke Extended JSON untuk tool MCP."""
    from bson import ObjectId

    def ubah(nilai: Any) -> Any:
        if isinstance(nilai, ObjectId):
            return {"$oid": str(nilai)}
        if isinstance(nilai, dict):
            return {k: ubah(v) for k, v in nilai.items()}
        if isinstance(nilai, list):
            return [ubah(v) for v in nilai]
        if isinstance(nilai, datetime):
            return nilai.isoformat()
        return nilai

    return ubah(dokumen)


async def panggil_mcp_insert_one(collection: str, dokumen: dict[str, Any]) -> None:
    """Panggil MCP insert-one (verifikasi tool terpanggil)."""
    sesi = await _dapatkan_sesi()
    pengaturan = ambil_pengaturan()
    payload = {
        "database": pengaturan.mongodb_database,
        "collection": collection,
        "document": _dokumen_ke_json_mcp(dokumen),
    }
    for nama_tool in ("insert-one", "insertOne"):
        try:
            hasil = await asyncio.wait_for(
                sesi.call_tool(nama_tool, payload),
                timeout=_TIMEOUT_MCP,
            )
            if hasil.isError:
                raise RuntimeError(
                    (hasil.content[0].text if hasil.content else "MCP insert error")[:200]
                )
            return
        except Exception as e:
            if nama_tool == "insertOne":
                raise e


async def panggil_mcp_update_one(
    collection: str,
    filter_query: dict[str, Any],
    update: dict[str, Any],
) -> None:
    """Panggil MCP update-one (verifikasi tool terpanggil)."""
    sesi = await _dapatkan_sesi()
    pengaturan = ambil_pengaturan()
    payload = {
        "database": pengaturan.mongodb_database,
        "collection": collection,
        "filter": _dokumen_ke_json_mcp(filter_query),
        "update": _dokumen_ke_json_mcp(update),
    }
    for nama_tool in ("update-one", "updateOne"):
        try:
            hasil = await asyncio.wait_for(
                sesi.call_tool(nama_tool, payload),
                timeout=_TIMEOUT_MCP,
            )
            if hasil.isError:
                raise RuntimeError(
                    (hasil.content[0].text if hasil.content else "MCP update error")[:200]
                )
            return
        except Exception as e:
            if nama_tool == "updateOne":
                raise e
