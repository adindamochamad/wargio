"""Wargio root agent — Google ADK / Agent Builder."""

from __future__ import annotations

from pathlib import Path

from google.adk.agents.llm_agent import Agent
from google.adk.tools import FunctionTool

from . import tools

_PROMPT = (
    Path(__file__).resolve().parent / "prompts" / "wargio_system.txt"
).read_text(encoding="utf-8")

root_agent = Agent(
    model="gemini-2.5-flash",
    name="wargio",
    description=(
        "AI business assistant for Indonesian warung owners — "
        "stok, hutang, restock, laporan penjualan via MongoDB Atlas."
    ),
    instruction=_PROMPT
    + "\n\nGunakan tools yang tersedia untuk mengambil data dari Atlas. "
    "Jangan buat-buat angka.",
    tools=[
        FunctionTool(tools.cek_stok_produk),
        FunctionTool(tools.cek_hutang_customer),
        FunctionTool(tools.daftar_restock_alert),
        FunctionTool(tools.laporan_penjualan),
    ],
)
