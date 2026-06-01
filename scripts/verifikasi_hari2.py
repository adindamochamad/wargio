#!/usr/bin/env python3
"""Verifikasi Definition of Done Hari 2 — 4 read intents."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
load_dotenv(ROOT / ".env")

QUERY_UJI = [
    ("check_stock", "stok indomie goreng berapa?", "indomie"),
    ("check_debt", "hutang Bu Sari berapa?", "Hutang"),
    ("restock_alert", "produk apa yang mau habis?", "restock"),
    ("sales_report", "pendapatan minggu ini berapa?", "Pendapatan"),
]


async def main() -> None:
    from app.main import aplikasi

    print("=== Verifikasi Hari 2 ===\n")
    gagal = 0
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://test", timeout=60.0) as klien:
        for intent, pesan, kata_kunci in QUERY_UJI:
            res = await klien.post(
                "/api/chat",
                json={"pesan": pesan},
                headers={"X-Session-Id": f"verifikasi-hari2-{intent}"},
            )
            if res.status_code != 200:
                print(f"  GAGAL {intent}: HTTP {res.status_code}")
                gagal += 1
                continue
            data = res.json()
            if data.get("intent") != intent:
                print(f"  GAGAL {intent}: intent={data.get('intent')}")
                gagal += 1
                continue
            if kata_kunci.lower() not in data.get("balasan", "").lower():
                print(f"  GAGAL {intent}: balasan tidak relevan")
                gagal += 1
                continue
            print(f"  OK {intent}: {data['balasan'][:80]}...")

    if gagal:
        print(f"\nGagal: {gagal}/{len(QUERY_UJI)}")
        sys.exit(1)
    print(f"\nSemua {len(QUERY_UJI)} intent read lolos.")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
