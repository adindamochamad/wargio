#!/usr/bin/env python3
"""Verifikasi Definition of Done Hari 2 — lengkap."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
load_dotenv(ROOT / ".env")

QUERY_UJI = [
    ("check_stock", {"message": "stok mie instan berapa?"}, "stok"),
    ("check_debt", {"message": "hutang bu sari total berapa?"}, "hutang"),
    ("restock_alert", {"message": "produk apa yang mau habis?"}, "restock"),
    ("sales_report", {"message": "pendapatan hari ini berapa?"}, "pendapatan"),
]

GAGAL: list[str] = []


def catat_lolos(pesan: str) -> None:
    print(f"  OK {pesan}")


def catat_gagal(pesan: str) -> None:
    print(f"  GAGAL {pesan}")
    GAGAL.append(pesan)


async def gate_intent_read(klien: AsyncClient) -> None:
    print("\n[GATE] 4 read intent via POST /api/chat")
    for intent, body, kata_kunci in QUERY_UJI:
        res = await klien.post(
            "/api/chat",
            json=body,
            headers={"X-Session-Id": f"verifikasi-hari2-{intent}"},
        )
        if res.status_code != 200:
            catat_gagal(f"{intent}: HTTP {res.status_code}")
            continue
        data = res.json()
        if data.get("intent") != intent:
            catat_gagal(f"{intent}: intent={data.get('intent')}")
            continue
        if kata_kunci.lower() not in data.get("balasan", "").lower():
            catat_gagal(f"{intent}: balasan tidak relevan")
            continue
        catat_lolos(f"{intent}: {data['balasan'][:70]}...")


async def gate_system_prompt() -> None:
    print("\n[GATE] System prompt Agent Builder")
    path = BACKEND / "app" / "prompts" / "wargio_system.txt"
    if not path.exists():
        catat_gagal("wargio_system.txt tidak ada")
        return
    isi = path.read_text(encoding="utf-8")
    if "Wargio" not in isi or "MCP" not in isi:
        catat_gagal("system prompt tidak lengkap")
        return
    catat_lolos(f"System prompt ada ({len(isi)} chars)")


async def gate_health_agent(klien: AsyncClient) -> None:
    print("\n[GATE] Health — agent_mode & mcp_mode")
    res = await klien.get("/api/health")
    if res.status_code != 200:
        catat_gagal(f"health HTTP {res.status_code}")
        return
    data = res.json()
    if not data.get("atlas"):
        catat_gagal("Atlas tidak connected")
        return
    if data.get("mcp_mode") not in ("pymongo_equivalent", "live_stdio"):
        catat_gagal(f"mcp_mode invalid: {data.get('mcp_mode')}")
        return
    if data.get("mcp_live_enabled") and not data.get("mcp"):
        catat_gagal("MCP live enabled tapi mcp=false")
        return
    if data.get("agent_mode") not in ("gemini", "intent_engine"):
        catat_gagal(f"agent_mode invalid: {data.get('agent_mode')}")
        return
    catat_lolos(
        f"agent_mode={data['agent_mode']}, mcp_mode={data['mcp_mode']}, "
        f"mcp_live={data.get('mcp_live_enabled')}, mcp_ok={data.get('mcp')}"
    )


async def gate_edge_case(klien: AsyncClient) -> None:
    print("\n[GATE] Edge case — stok berapa?")
    res = await klien.post(
        "/api/chat",
        json={"pesan": "stok berapa?"},
        headers={"X-Session-Id": "verifikasi-hari2-edge"},
    )
    data = res.json()
    if "Produk mana" not in data.get("balasan", ""):
        catat_gagal("stok berapa? tidak minta spesifikasi produk")
        return
    catat_lolos("stok berapa? → minta spesifikasi produk")


async def gate_mcp_tools_layer() -> None:
    print("\n[GATE] Layer MCP-equivalent tools")
    from app.services import atlas_tools

    if not hasattr(atlas_tools, "mcp_find"):
        catat_gagal("mcp_find tidak ada")
        return
    if not hasattr(atlas_tools, "mcp_aggregate"):
        catat_gagal("mcp_aggregate tidak ada")
        return
    catat_lolos("atlas_tools.mcp_find + mcp_aggregate tersedia")


async def main() -> None:
    from app.main import aplikasi

    print("=== Verifikasi Hari 2 (Full) ===")
    await gate_system_prompt()
    await gate_mcp_tools_layer()

    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://test", timeout=60.0) as klien:
        await gate_health_agent(klien)
        await gate_intent_read(klien)
        await gate_edge_case(klien)

    if GAGAL:
        print(f"\nGagal: {len(GAGAL)}")
        for g in GAGAL:
            print(f"  - {g}")
        sys.exit(1)

    print(f"\nSemua gate Hari 2 lolos ({len(QUERY_UJI) + 4} checks).")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
