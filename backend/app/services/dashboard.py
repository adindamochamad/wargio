"""Agregasi data dashboard mini — query Atlas langsung (tanpa MCP live)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from pymongo.asynchronous.database import AsyncDatabase

from app.schemas.dashboard import (
    CustomerHutangRingkas,
    ProdukStokKritis,
    ResponsDashboard,
)


async def ambil_ringkasan_dashboard(db: AsyncDatabase) -> ResponsDashboard:
    """
    Kumpulkan stok kritis, hutang, dan penjualan hari ini.
    Query PyMongo langsung agar UI cepat dan tidak bergantung MCP stdio.
    """
    filter_rendah = {"$expr": {"$lte": ["$stock_current", "$stock_minimum"]}}
    kursor_produk = db.products.find(filter_rendah).sort("stock_current", 1).limit(8)
    produk_rendah = await kursor_produk.to_list(length=8)

    stok_kritis = [
        ProdukStokKritis(
            nama=p["name"],
            stok_saat_ini=p["stock_current"],
            stok_minimum=p["stock_minimum"],
            satuan=p.get("unit", "pcs"),
        )
        for p in produk_rendah
    ]

    kursor_cust = (
        db.customers.find({"debt_total": {"$gt": 0}})
        .sort("debt_total", -1)
        .limit(20)
    )
    customer_berhutang = await kursor_cust.to_list(length=20)
    total_hutang = sum(c.get("debt_total", 0) for c in customer_berhutang)
    teratas = [
        CustomerHutangRingkas(nama=c["name"], total_hutang=c.get("debt_total", 0))
        for c in customer_berhutang[:5]
    ]

    zona = ZoneInfo("Asia/Jakarta")
    sekarang = datetime.now(zona)
    awal_hari = sekarang.replace(hour=0, minute=0, second=0, microsecond=0)
    awal_utc = awal_hari.astimezone(timezone.utc)
    akhir_utc = sekarang.astimezone(timezone.utc)

    pipeline: list[dict[str, Any]] = [
        {
            "$match": {
                "type": "sale",
                "created_at": {"$gte": awal_utc, "$lte": akhir_utc},
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
    kursor_agg = await db.transactions.aggregate(pipeline)
    agg = await kursor_agg.to_list(length=1)
    omzet = 0
    jumlah_tx = 0
    if agg:
        omzet = int(agg[0].get("total_omzet", 0))
        jumlah_tx = int(agg[0].get("jumlah_transaksi", 0))

    return ResponsDashboard(
        stok_kritis=stok_kritis,
        jumlah_produk_kritis=len(stok_kritis),
        total_hutang_aktif=total_hutang,
        jumlah_customer_berhutang=len(customer_berhutang),
        customer_hutang_teratas=teratas,
        omzet_hari_ini=omzet,
        jumlah_transaksi_hari_ini=jumlah_tx,
    )
