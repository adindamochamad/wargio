"""Alur konfirmasi write intent — simpan di context sesi."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from pymongo.asynchronous.database import AsyncDatabase

from app.services.sesi import ambil_context, set_context

# Draft write kedaluwarsa setelah 30 menit tanpa konfirmasi
BATAS_KEDALUWARSA_PENDING = timedelta(minutes=30)

# Kata konfirmasi / batal
KATA_KONFIRMASI = frozenset({
    "ya", "iya", "ok", "oke", "setuju", "lanjut", "lanjutkan",
    "konfirmasi", "benar", "betul", "sip", "yoi",
})
KATA_BATAL = frozenset({
    "tidak", "batal", "cancel", "gak jadi", "ga jadi", "jangan",
})


def normalisasi_konfirmasi(pesan: str) -> str:
    return pesan.lower().strip().rstrip(".,!?")


def adalah_konfirmasi(pesan: str) -> bool:
    teks = normalisasi_konfirmasi(pesan)
    if teks in KATA_KONFIRMASI:
        return True
    return bool(re.match(r"^(ya|iya|ok|setuju)\s*,?\s*$", teks))


def adalah_batal(pesan: str) -> bool:
    teks = normalisasi_konfirmasi(pesan)
    return teks in KATA_BATAL or teks.startswith("batal")


async def simpan_pending(
    db: AsyncDatabase,
    session_id: str,
    data_pending: dict[str, Any],
) -> None:
    """Simpan aksi write yang menunggu konfirmasi user."""
    data_pending["dibuat_pada"] = datetime.now(timezone.utc).isoformat()
    ctx = await ambil_context(db, session_id)
    ctx["pending_write"] = data_pending
    await set_context(db, session_id, ctx)


async def hapus_pending(db: AsyncDatabase, session_id: str) -> None:
    ctx = await ambil_context(db, session_id)
    ctx.pop("pending_write", None)
    await set_context(db, session_id, ctx)


def _pending_kedaluwarsa(data_pending: dict[str, Any]) -> bool:
    teks_waktu = data_pending.get("dibuat_pada")
    if not teks_waktu:
        return False
    try:
        dibuat = datetime.fromisoformat(teks_waktu)
        if dibuat.tzinfo is None:
            dibuat = dibuat.replace(tzinfo=timezone.utc)
    except ValueError:
        return False
    return datetime.now(timezone.utc) - dibuat > BATAS_KEDALUWARSA_PENDING


async def ambil_pending(
    db: AsyncDatabase,
    session_id: str,
) -> Optional[dict[str, Any]]:
    """Ambil pending; hapus otomatis jika sudah kedaluwarsa."""
    ctx = await ambil_context(db, session_id)
    pending = ctx.get("pending_write")
    if not pending:
        return None
    if _pending_kedaluwarsa(pending):
        await hapus_pending(db, session_id)
        return None
    return pending


def format_ringkasan_penjualan(draft: dict[str, Any]) -> str:
    from app.util.format import format_rupiah

    baris = []
    for item in draft["items"]:
        baris.append(
            f"  - {item['qty']}x **{item['product_name']}** "
            f"@ {format_rupiah(item['price'])} = {format_rupiah(item['subtotal'])}"
        )
    total_teks = format_rupiah(draft["total"])
    metode = draft.get("payment_method", "tunai")
    baris_customer = ""
    if metode == "hutang" and draft.get("customer_name"):
        baris_customer = f"\nCustomer: **{draft['customer_name']}** (bon/hutang)\n"
    return (
        "Konfirmasi penjualan ini, Bu/Pak?\n"
        + "\n".join(baris)
        + f"\n\n**Total: {total_teks}** ({metode})"
        + baris_customer
        + "\n\nBalas **ya** untuk mencatat, atau **batal** untuk membatalkan."
    )


def format_ringkasan_pembayaran(draft: dict[str, Any]) -> str:
    from app.util.format import format_rupiah

    jumlah = format_rupiah(draft["amount"])
    sisa = format_rupiah(draft["debt_after"])
    return (
        f"Konfirmasi pembayaran hutang **{draft['customer_name']}**?\n"
        f"  - Jumlah bayar: **{jumlah}**\n"
        f"  - Sisa hutang setelah bayar: **{sisa}**\n\n"
        "Balas **ya** untuk mencatat, atau **batal** untuk membatalkan."
    )
