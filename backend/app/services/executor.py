"""Orkestrasi intent — routing ke handler Atlas."""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from pymongo.asynchronous.database import AsyncDatabase

from app.services.agent_gemini import tentukan_intent
from app.services.intent_handlers import (
    handle_check_debt,
    handle_check_stock,
    handle_debt_collection,
    handle_restock_alert,
    handle_sales_forecast,
    handle_sales_report,
)
from app.services.klasifikasi import klasifikasi_intent
from app.services.konfirmasi import (
    adalah_batal,
    adalah_konfirmasi,
    ambil_pending,
    hapus_pending,
)

_INTENT_WRITE = frozenset({"record_sale", "record_payment"})
from app.services.write_handlers import (
    eksekusi_record_payment,
    eksekusi_record_sale,
    siapkan_record_payment,
    siapkan_record_sale,
)
from app.util.lokalisasi import konteks_bahasa, t

MAX_COBA_ULANG = 1


async def jalankan_dengan_retry(
    db: AsyncDatabase,
    intent: str,
    pesan: str,
    session_id: str,
) -> tuple[str, list[str]]:
    """Eksekusi handler dengan retry 1x jika error Atlas."""
    for percobaan in range(MAX_COBA_ULANG + 1):
        try:
            return await _jalankan_intent(db, intent, pesan, session_id)
        except Exception as e:
            if percobaan >= MAX_COBA_ULANG:
                raise e
            await asyncio.sleep(0.5)
    raise RuntimeError("retry gagal")


async def _proses_konfirmasi_tunda(
    db: AsyncDatabase,
    session_id: str,
    pesan: str,
) -> Optional[dict[str, Any]]:
    """Jika ada pending write, proses konfirmasi/batal."""
    pending = await ambil_pending(db, session_id)
    if not pending:
        return None

    if adalah_batal(pesan):
        await hapus_pending(db, session_id)
        return {
            "balasan": t(
                "Oke, dibatalkan. Tidak ada perubahan di database.",
                "Cancelled. No changes were made to the database.",
            ),
            "intent": pending.get("tipe"),
            "actions_taken": ["konfirmasi_dibatalkan"],
            "classification_mode": "regex",
        }

    # Draft baru menggantikan pending lama (mis. user ubah pikiran)
    intent_baru = klasifikasi_intent(pesan)
    if intent_baru in _INTENT_WRITE:
        await hapus_pending(db, session_id)
        return None

    if not adalah_konfirmasi(pesan):
        return {
            "balasan": t(
                "Masih ada transaksi yang menunggu konfirmasi. "
                "Balas **ya** untuk melanjutkan atau **batal** untuk membatalkan.",
                "A transaction is still awaiting confirmation. "
                "Reply **yes** to continue or **cancel** to abort.",
            ),
            "intent": pending.get("tipe"),
            "actions_taken": ["menunggu_konfirmasi"],
            "classification_mode": "regex",
        }

    tipe = pending.get("tipe")
    if tipe == "record_sale":
        balasan, aksi = await eksekusi_record_sale(db, session_id, pending)
    elif tipe == "record_payment":
        balasan, aksi = await eksekusi_record_payment(db, session_id, pending)
    else:
        await hapus_pending(db, session_id)
        return {
            "balasan": t(
                "Aksi tidak dikenali, dibatalkan.",
                "Unknown action — cancelled.",
            ),
            "intent": None,
            "actions_taken": ["error"],
            "classification_mode": "regex",
        }

    return {
        "balasan": balasan,
        "intent": tipe,
        "actions_taken": [*aksi, "konfirmasi_diterima"],
        "classification_mode": "regex",
    }


async def _jalankan_intent(
    db: AsyncDatabase,
    intent: str,
    pesan: str,
    session_id: str,
) -> tuple[str, list[str]]:
    if intent == "check_stock":
        return await handle_check_stock(db, pesan)
    if intent == "check_debt":
        return await handle_check_debt(db, pesan)
    if intent == "restock_alert":
        return await handle_restock_alert(db)
    if intent == "sales_report":
        return await handle_sales_report(db, pesan)
    if intent == "record_sale":
        return await siapkan_record_sale(db, session_id, pesan)
    if intent == "record_payment":
        return await siapkan_record_payment(db, session_id, pesan)
    if intent == "debt_collection":
        return await handle_debt_collection(db)
    if intent == "sales_forecast":
        return await handle_sales_forecast(db)
    return (
        t(
            "Maaf, saya belum paham maksudnya. Coba tanya tentang stok, hutang, "
            "penjualan, restock, atau laporan.",
            "Sorry, I didn't understand. Try asking about stock, debt, "
            "sales, restock, or reports.",
        ),
        [],
    )


async def proses_pesan(
    db: AsyncDatabase,
    pesan: str,
    session_id: str,
    *,
    kode_bahasa: str = "id",
) -> dict[str, Any]:
    """Klasifikasi + eksekusi intent, return balasan terstruktur."""
    with konteks_bahasa(kode_bahasa):
        hasil_konfirmasi = await _proses_konfirmasi_tunda(db, session_id, pesan)
        if hasil_konfirmasi:
            return hasil_konfirmasi

        intent, mode_klasifikasi = await tentukan_intent(pesan)
        try:
            balasan, aksi = await jalankan_dengan_retry(
                db, intent, pesan, session_id
            )
        except Exception:
            balasan = t(
                "Ada gangguan teknis saat akses database. Coba lagi sebentar ya.",
                "Technical issue accessing the database. Please try again shortly.",
            )
            aksi = ["error_atlas"]
            intent = intent if intent != "unknown" else "error"

        if mode_klasifikasi == "gemini" and "agent:gemini" not in aksi:
            aksi = ["agent:gemini", *aksi]

        return {
            "balasan": balasan,
            "intent": intent if intent != "unknown" else None,
            "actions_taken": aksi,
            "classification_mode": mode_klasifikasi,
        }
