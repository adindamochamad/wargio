#!/usr/bin/env python3
"""Verifikasi MCP live — pool stdio + find/aggregate."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
load_dotenv(ROOT / ".env")

# Paksa MCP live untuk skrip ini
os.environ["MCP_LIVE_ENABLED"] = "true"


async def main() -> None:
    from app.config import ambil_pengaturan

    ambil_pengaturan.cache_clear()
    pengaturan = ambil_pengaturan()

    print("=== Verifikasi MCP Live ===\n")
    gagal = 0

    if not pengaturan.mcp_live_enabled:
        print("  GAGAL: MCP_LIVE_ENABLED tidak true")
        sys.exit(1)

    from app.services.mcp_klien import (
        mulai_pool_mcp,
        panggil_mcp_aggregate,
        panggil_mcp_find,
        tutup_pool_mcp,
    )

    print("[1] Mulai pool MCP...")
    if not await mulai_pool_mcp():
        print("  GAGAL: pool MCP tidak bisa dibuka")
        sys.exit(1)
    print("  OK pool MCP aktif")

    try:
        print("\n[2] MCP find products (stok rendah)...")
        teks = await panggil_mcp_find(
            "products",
            {"$expr": {"$lte": ["$stock_current", "$stock_minimum"]}},
            limit=3,
        )
        if "documents" not in teks.lower():
            print(f"  GAGAL: respons tidak valid: {teks[:100]}")
            gagal += 1
        else:
            print(f"  OK {teks[:80]}...")

        print("\n[3] MCP aggregate transactions...")
        pipeline = [
            {"$match": {"type": "sale"}},
            {"$group": {"_id": None, "total": {"$sum": "$total"}, "n": {"$sum": 1}}},
        ]
        agg = await panggil_mcp_aggregate("transactions", pipeline)
        if not agg:
            print("  GAGAL: aggregate kosong")
            gagal += 1
        elif "n" in agg[0] or "total" in agg[0]:
            print(f"  OK aggregate: {agg[0].get('n', '?')} transaksi, total={agg[0].get('total', '?')}")
        else:
            print(f"  GAGAL: field tidak dikenal: {list(agg[0].keys())}")
            gagal += 1

        print("\n[4] MCP standalone (verifikasi_mcp.mjs)...")
        import subprocess

        skrip_mcp = ROOT / "scripts" / "verifikasi_mcp.mjs"
        # stdout/stderr ke DEVNULL — pipe ke parent memicu EPIPE pada MCP stdio transport
        hasil = subprocess.run(
            ["node", str(skrip_mcp)],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=180,
        )
        if hasil.returncode != 0:
            print(f"  GAGAL: verifikasi_mcp.mjs exit {hasil.returncode}")
            gagal += 1
        else:
            print("  OK MCP standalone find stok rendah")

    finally:
        await tutup_pool_mcp()

    if gagal:
        print(f"\nGagal: {gagal} check")
        sys.exit(1)
    print("\nSemua gate MCP live lolos.")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
