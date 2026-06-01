"""
Tools ADK Wargio — operasi setara MCP find/aggregate ke MongoDB Atlas.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from pymongo import MongoClient

# Muat .env root repo saat dev lokal
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

_klien: Optional[MongoClient] = None


def _database():
    """Koneksi sync MongoDB untuk tools ADK."""
    global _klien
    uri = os.environ.get("MONGODB_URI", "")
    nama_db = os.environ.get("MONGODB_DATABASE", "wargio_demo")
    if not uri:
        raise RuntimeError("MONGODB_URI belum dikonfigurasi")
    if _klien is None:
        _klien = MongoClient(uri)
    return _klien[nama_db]


def _format_rupiah(jumlah: int | float) -> str:
    bilangan = int(round(jumlah))
    return f"Rp {f'{bilangan:,}'.replace(',', '.')}"


async def cek_stok_produk(nama_produk: str) -> str:
    """
    Cek stok produk warung berdasarkan nama atau alias (MCP find products).

    Args:
        nama_produk: Nama produk, contoh 'indomie' atau 'aqua'.
    """
    db = _database()
    teks = nama_produk.lower().strip()
    filter_query = {
        "$or": [
            {"name": {"$regex": re.escape(teks), "$options": "i"}},
            {"name_aliases": {"$regex": re.escape(teks), "$options": "i"}},
        ]
    }
    hasil = list(db.products.find(filter_query).limit(3))
    if not hasil:
        return f'Produk "{nama_produk}" tidak ditemukan.'
    if len(hasil) > 1:
        baris = "\n".join(
            f"  {i + 1}. {p['name']} (stok: {p['stock_current']})"
            for i, p in enumerate(hasil)
        )
        return f"Maksudnya yang mana?\n{baris}"
    p = hasil[0]
    stok, minimum = p["stock_current"], p["stock_minimum"]
    status = "aman" if stok > minimum else "hampir habis — perlu restock"
    return (
        f"Stok **{p['name']}**: {stok} {p['unit']} "
        f"(minimum {minimum}). Status: {status}."
    )


async def cek_hutang_customer(nama_customer: str) -> str:
    """
    Cek total hutang customer (MCP find customers).

    Args:
        nama_customer: Nama customer, contoh 'Bu Sari'.
    """
    db = _database()
    hasil = list(
        db.customers.find({"name": {"$regex": nama_customer, "$options": "i"}}).limit(3)
    )
    if not hasil:
        return f'Customer "{nama_customer}" tidak ditemukan.'
    if len(hasil) > 1:
        baris = "\n".join(f"  {i + 1}. {c['name']}" for i, c in enumerate(hasil))
        return f"Ada beberapa yang cocok:\n{baris}"
    cust = hasil[0]
    total = cust.get("debt_total", 0)
    if total <= 0:
        return f"{cust['name']} tidak punya hutang aktif."
    belum_bayar = [h for h in cust.get("debt_history", []) if not h.get("paid")]
    rincian = "\n".join(
        f"  - {_format_rupiah(h['amount'])} ({h.get('description', '-')})"
        for h in belum_bayar[:5]
    )
    return (
        f"Hutang **{cust['name']}** total **{_format_rupiah(total)}**.\n"
        f"Rincian:\n{rincian or '  (tidak ada detail)'}"
    )


async def daftar_restock_alert() -> str:
    """Daftar produk yang perlu restock — stok <= minimum (MCP find + sort)."""
    db = _database()
    filter_rendah = {"$expr": {"$lte": ["$stock_current", "$stock_minimum"]}}
    hasil = list(db.products.find(filter_rendah).sort("stock_current", 1).limit(10))
    if not hasil:
        return "Semua produk masih aman, tidak ada yang perlu restock urgent."
    baris = []
    for p in hasil:
        selisih = p["stock_minimum"] - p["stock_current"]
        baris.append(
            f"  - **{p['name']}**: {p['stock_current']}/{p['stock_minimum']} "
            f"{p['unit']} (kurang {max(selisih, 0)})"
        )
    return f"Produk yang perlu restock ({len(hasil)}):\n" + "\n".join(baris)


async def laporan_penjualan(rentang: str = "hari_ini") -> str:
    """
    Laporan pendapatan penjualan (MCP aggregate transactions).

    Args:
        rentang: 'hari_ini' atau 'minggu_ini'.
    """
    db = _database()
    zona = ZoneInfo("Asia/Jakarta")
    sekarang = datetime.now(zona)
    awal_hari = sekarang.replace(hour=0, minute=0, second=0, microsecond=0)
    if rentang == "minggu_ini":
        awal = awal_hari - timedelta(days=7)
        label = "7 hari terakhir"
    else:
        awal = awal_hari
        label = "hari ini"

    pipeline: list[dict[str, Any]] = [
        {
            "$match": {
                "type": "sale",
                "created_at": {
                    "$gte": awal.astimezone(timezone.utc),
                    "$lte": sekarang.astimezone(timezone.utc),
                },
            }
        },
        {
            "$group": {
                "_id": None,
                "total_omzet": {"$sum": "$total"},
                "jumlah_transaksi": {"$sum": 1},
            }
        },
    ]
    agg = list(db.transactions.aggregate(pipeline))
    if not agg:
        return f"Belum ada penjualan untuk {label}."
    data = agg[0]
    return (
        f"Pendapatan **{label}**: **{_format_rupiah(data['total_omzet'])}** "
        f"dari {data['jumlah_transaksi']} transaksi."
    )
