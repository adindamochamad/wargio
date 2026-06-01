"""Handler intent Tier 1 read."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

from pymongo.asynchronous.database import AsyncDatabase

from app.services.klasifikasi import ekstrak_nama_customer, ekstrak_nama_produk
from app.services.produk import resolve_produk_tunggal
from app.util.format import format_rupiah, tanggal_indonesia


async def handle_check_stock(
    db: AsyncDatabase,
    pesan: str,
) -> tuple[str, list[str]]:
    """Cek stok produk — find products."""
    kata_kunci = ekstrak_nama_produk(pesan)
    if not kata_kunci:
        return (
            "Produk mana yang ingin dicek stoknya, Bu/Pak? "
            "Contoh: \"stok mie instan berapa?\"",
            ["minta_spesifikasi_produk"],
        )

    produk, opsi = await resolve_produk_tunggal(db, kata_kunci)
    if opsi:
        baris = "\n".join(
            f"  {i + 1}. {p['name']} (stok: {p['stock_current']})"
            for i, p in enumerate(opsi)
        )
        return (
            f"Maksudnya yang mana?\n{baris}",
            ["disambiguasi_produk"],
        )
    if not produk:
        return (
            f"Produk \"{kata_kunci}\" tidak ditemukan. Coba sebut nama yang lebih spesifik.",
            ["produk_tidak_ditemukan"],
        )

    stok = produk["stock_current"]
    minimum = produk["stock_minimum"]
    status = "aman"
    if stok <= minimum:
        status = "hampir habis — perlu restock"
    elif stok <= minimum * 1.2:
        status = "mendekati minimum"

    balasan = (
        f"Stok **{produk['name']}**: {stok} {produk['unit']} "
        f"(minimum {minimum}). Status: {status}."
    )
    return balasan, ["find_products", "compare_minimum"]


async def handle_check_debt(
    db: AsyncDatabase,
    pesan: str,
) -> tuple[str, list[str]]:
    """Cek hutang customer — find customers."""
    nama = ekstrak_nama_customer(pesan)
    if not nama:
        return (
            "Hutang siapa yang ingin dicek? Contoh: \"hutang Bu Sari berapa?\"",
            ["minta_nama_customer"],
        )

    kursor = db.customers.find({"name": {"$regex": nama, "$options": "i"}}).limit(3)
    hasil = await kursor.to_list(length=3)

    if len(hasil) == 0:
        return (
            f"Customer \"{nama}\" tidak ditemukan.",
            ["customer_tidak_ditemukan"],
        )
    if len(hasil) > 1:
        baris = "\n".join(f"  {i + 1}. {c['name']}" for i, c in enumerate(hasil))
        return f"Ada beberapa yang cocok:\n{baris}", ["disambiguasi_customer"]

    cust = hasil[0]
    total = cust.get("debt_total", 0)
    if total <= 0:
        return f"{cust['name']} tidak punya hutang aktif.", ["find_customers"]

    belum_bayar = [h for h in cust.get("debt_history", []) if not h.get("paid")]
    rincian = "\n".join(
        f"  - {format_rupiah(h['amount'])} ({h.get('description', '-')})"
        for h in belum_bayar[:5]
    )
    return (
        f"Hutang **{cust['name']}** total **{format_rupiah(total)}**.\n"
        f"Rincian:\n{rincian or '  (tidak ada detail)'}",
        ["find_customers", "hitung_total_hutang"],
    )


async def handle_restock_alert(db: AsyncDatabase) -> tuple[str, list[str]]:
    """Produk stok rendah — find + sort urgency."""
    filter_rendah = {"$expr": {"$lte": ["$stock_current", "$stock_minimum"]}}
    kursor = db.products.find(filter_rendah).sort("stock_current", 1).limit(10)
    hasil = await kursor.to_list(length=10)

    if not hasil:
        return "Semua produk masih aman, tidak ada yang perlu restock urgent.", ["find_products"]

    baris = []
    for p in hasil:
        selisih = p["stock_minimum"] - p["stock_current"]
        baris.append(
            f"  - **{p['name']}**: {p['stock_current']}/{p['stock_minimum']} "
            f"{p['unit']} (kurang {max(selisih, 0)})"
        )
    return (
        f"Produk yang perlu restock ({len(hasil)}):\n" + "\n".join(baris),
        ["find_products", "rank_urgency"],
    )


async def handle_sales_report(
    db: AsyncDatabase,
    pesan: str,
) -> tuple[str, list[str]]:
    """Laporan penjualan hari ini — aggregate transactions."""
    zona = ZoneInfo("Asia/Jakarta")
    sekarang = datetime.now(zona)
    awal_hari = sekarang.replace(hour=0, minute=0, second=0, microsecond=0)

    # Deteksi rentang sederhana
    teks = pesan.lower()
    if "minggu" in teks:
        awal = awal_hari - timedelta(days=7)
        label = "7 hari terakhir"
    else:
        awal = awal_hari
        label = f"hari ini ({tanggal_indonesia(sekarang.astimezone(timezone.utc))})"

    # Query pakai UTC agar match dokumen seed
    awal_utc = awal.astimezone(timezone.utc)
    sekarang_utc = sekarang.astimezone(timezone.utc)

    pipeline: list[dict[str, Any]] = [
        {
            "$match": {
                "type": "sale",
                "created_at": {"$gte": awal_utc, "$lte": sekarang_utc},
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
    kursor = await db.transactions.aggregate(pipeline)
    agg = await kursor.to_list(length=1)

    if not agg:
        return f"Belum ada penjualan untuk {label}.", ["aggregate_transactions"]

    data = agg[0]
    return (
        f"Pendapatan **{label}**: **{format_rupiah(data['total_omzet'])}** "
        f"dari {data['jumlah_transaksi']} transaksi.",
        ["aggregate_transactions", "format_laporan"],
    )
