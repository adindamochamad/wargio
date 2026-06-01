"""Orkestrasi intent — routing ke handler Atlas."""

from __future__ import annotations

import asyncio
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.services.intent_handlers import (
    handle_check_debt,
    handle_check_stock,
    handle_restock_alert,
    handle_sales_report,
)
from app.services.klasifikasi import klasifikasi_intent

MAX_COBA_ULANG = 1


async def jalankan_dengan_retry(
    db: AsyncDatabase,
    intent: str,
    pesan: str,
) -> tuple[str, list[str]]:
    """Eksekusi handler dengan retry 1x jika error Atlas."""
    for percobaan in range(MAX_COBA_ULANG + 1):
        try:
            return await _jalankan_intent(db, intent, pesan)
        except Exception as e:
            if percobaan >= MAX_COBA_ULANG:
                raise e
            await asyncio.sleep(0.5)
    raise RuntimeError("retry gagal")


async def _jalankan_intent(
    db: AsyncDatabase,
    intent: str,
    pesan: str,
) -> tuple[str, list[str]]:
    if intent == "check_stock":
        return await handle_check_stock(db, pesan)
    if intent == "check_debt":
        return await handle_check_debt(db, pesan)
    if intent == "restock_alert":
        return await handle_restock_alert(db)
    if intent == "sales_report":
        return await handle_sales_report(db, pesan)
    return (
        "Maaf, saya belum paham maksudnya. Coba tanya tentang stok, hutang, "
        "restock, atau laporan penjualan.",
        [],
    )


async def proses_pesan(
    db: AsyncDatabase,
    pesan: str,
) -> dict[str, Any]:
    """Klasifikasi + eksekusi intent, return balasan terstruktur."""
    intent = klasifikasi_intent(pesan)
    try:
        balasan, aksi = await jalankan_dengan_retry(db, intent, pesan)
    except Exception:
        balasan = "Ada gangguan teknis saat akses database. Coba lagi sebentar ya."
        aksi = ["error_atlas"]
        intent = intent if intent != "unknown" else "error"

    return {
        "balasan": balasan,
        "intent": intent if intent != "unknown" else None,
        "actions_taken": aksi,
    }
