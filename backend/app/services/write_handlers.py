"""Handler write intent — record_sale dan record_payment dengan konfirmasi."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from bson import ObjectId
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.database import AsyncDatabase

from app.services.atlas_tools import mcp_insert_one, mcp_update_one
from app.services.ekstrak_entitas import (
    ekstrak_item_penjualan,
    ekstrak_pembayaran_hutang,
    pisahkan_customer_dari_penjualan,
)
from app.services.konfirmasi import (
    format_ringkasan_pembayaran,
    format_ringkasan_penjualan,
    hapus_pending,
    simpan_pending,
)
from app.services.produk import resolve_produk_tunggal
from app.services.transaksi_atomik import jalankan_dalam_transaksi
from app.util.format import format_rupiah


async def _resolve_customer(
    db: AsyncDatabase,
    nama: str,
) -> tuple[Optional[dict[str, Any]], list[dict[str, Any]]]:
    from app.services.atlas_tools import mcp_find

    hasil, _ = await mcp_find(
        db,
        "customers",
        {"name": {"$regex": nama, "$options": "i"}},
        limit=3,
    )
    if len(hasil) == 1:
        return hasil[0], []
    if len(hasil) > 1:
        return None, hasil
    return None, []


async def siapkan_record_sale(
    db: AsyncDatabase,
    session_id: str,
    pesan: str,
) -> tuple[str, list[str]]:
    """Validasi penjualan, simpan draft, minta konfirmasi."""
    _, nama_customer_hutang = pisahkan_customer_dari_penjualan(pesan)
    item_mentah = ekstrak_item_penjualan(pesan)
    if not item_mentah:
        return (
            "Format penjualan kurang jelas. Contoh: "
            "\"tadi jual 3 aqua sama 2 rokok\" atau "
            "\"jual 2 indomie bon Bu Sari\"",
            ["minta_detail_penjualan"],
        )

    item_siap: list[dict[str, Any]] = []
    aksi = ["mcp:find"]

    for qty, nama_produk in item_mentah:
        if qty <= 0:
            return (
                f"Jumlah tidak valid untuk \"{nama_produk}\". Harus lebih dari 0.",
                ["validasi_qty_gagal"],
            )

        produk, opsi, aksi_cari = await resolve_produk_tunggal(db, nama_produk)
        aksi.extend(aksi_cari)

        if opsi:
            baris = "\n".join(
                f"  {i + 1}. {p['name']}" for i, p in enumerate(opsi)
            )
            return (
                f"Produk \"{nama_produk}\" ambigu. Maksudnya yang mana?\n{baris}",
                [*aksi, "disambiguasi_produk"],
            )
        if not produk:
            return (
                f"Produk \"{nama_produk}\" tidak ditemukan.",
                [*aksi, "produk_tidak_ditemukan"],
            )
        if produk["stock_current"] < qty:
            return (
                f"Stok **{produk['name']}** tidak cukup. "
                f"Tersedia {produk['stock_current']} {produk['unit']}, diminta {qty}.",
                [*aksi, "stok_tidak_cukup"],
            )

        harga = produk["price_sell"]
        item_siap.append({
            "product_id": str(produk["_id"]),
            "product_name": produk["name"],
            "sku": produk.get("sku", ""),
            "qty": qty,
            "price": harga,
            "subtotal": harga * qty,
            "stock_sebelum": produk["stock_current"],
        })

    total = sum(i["subtotal"] for i in item_siap)
    teks = pesan.lower()
    metode = "hutang" if "hutang" in teks or "bon" in teks else "tunai"

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None

    if metode == "hutang":
        if not nama_customer_hutang:
            return (
                "Penjualan bon/hutang perlu nama customer. "
                "Contoh: \"jual 2 indomie bon Bu Sari\"",
                ["minta_nama_customer_hutang"],
            )
        customer, opsi_cust = await _resolve_customer(db, nama_customer_hutang)
        aksi.extend(["mcp:find"])
        if opsi_cust:
            baris = "\n".join(
                f"  {i + 1}. {c['name']}" for i, c in enumerate(opsi_cust)
            )
            return (
                f"Customer \"{nama_customer_hutang}\" ambigu:\n{baris}",
                [*aksi, "disambiguasi_customer"],
            )
        if not customer:
            return (
                f"Customer \"{nama_customer_hutang}\" tidak ditemukan.",
                [*aksi, "customer_tidak_ditemukan"],
            )
        customer_id = str(customer["_id"])
        customer_name = customer["name"]

    draft = {
        "tipe": "record_sale",
        "items": item_siap,
        "total": total,
        "payment_method": metode,
        "customer_id": customer_id,
        "customer_name": customer_name,
    }
    await simpan_pending(db, session_id, draft)

    return format_ringkasan_penjualan(draft), [*aksi, "minta_konfirmasi"]


async def eksekusi_record_sale(
    db: AsyncDatabase,
    session_id: str,
    draft: dict[str, Any],
) -> tuple[str, list[str]]:
    """Eksekusi penjualan setelah user konfirmasi (transaksi atomik)."""
    sekarang = datetime.now(timezone.utc)
    aksi_utama = ["mcp:insertOne", "mcp:updateOne"]

    dokumen_tx = {
        "type": "sale",
        "items": [
            {
                "product_id": ObjectId(i["product_id"]),
                "product_name": i["product_name"],
                "qty": i["qty"],
                "price": i["price"],
                "subtotal": i["subtotal"],
            }
            for i in draft["items"]
        ],
        "total": draft["total"],
        "payment_method": draft["payment_method"],
        "customer_id": ObjectId(draft["customer_id"]) if draft.get("customer_id") else None,
        "notes": "Catat via Wargio agent",
        "created_at": sekarang,
    }

    async def _jalankan(sesi: AsyncClientSession) -> list[str]:
        aksi_dalam: list[str] = []
        _, aksi_ins = await mcp_insert_one(
            db, "transactions", dokumen_tx, session=sesi
        )
        aksi_dalam.extend(aksi_ins)

        for item in draft["items"]:
            _, aksi_upd = await mcp_update_one(
                db,
                "products",
                {"_id": ObjectId(item["product_id"])},
                {
                    "$inc": {"stock_current": -item["qty"]},
                    "$set": {"updated_at": sekarang},
                },
                session=sesi,
            )
            aksi_dalam.extend(aksi_upd)

        if draft["payment_method"] == "hutang" and draft.get("customer_id"):
            ringkasan_item = ", ".join(
                f"{i['qty']}x {i['product_name']}" for i in draft["items"]
            )
            entri_hutang = {
                "amount": draft["total"],
                "description": f"Bon penjualan: {ringkasan_item}",
                "date": sekarang,
                "paid": False,
                "paid_date": None,
            }
            _, aksi_hutang = await mcp_update_one(
                db,
                "customers",
                {"_id": ObjectId(draft["customer_id"])},
                {
                    "$inc": {"debt_total": draft["total"]},
                    "$push": {"debt_history": entri_hutang},
                },
                session=sesi,
            )
            aksi_dalam.extend(aksi_hutang)

        return aksi_dalam

    try:
        aksi_transaksi = await jalankan_dalam_transaksi(db, _jalankan)
    except Exception:
        return (
            "Gagal mencatat penjualan — perubahan dibatalkan. Coba lagi sebentar.",
            ["error_transaksi_atomik"],
        )

    await hapus_pending(db, session_id)

    baris = "\n".join(
        f"  - {i['qty']}x {i['product_name']}" for i in draft["items"]
    )
    teks_hutang = ""
    if draft["payment_method"] == "hutang" and draft.get("customer_name"):
        teks_hutang = f"\nHutang **{draft['customer_name']}** bertambah **{format_rupiah(draft['total'])}**."

    return (
        f"Penjualan **berhasil dicatat**.\n{baris}\n"
        f"Total: **{format_rupiah(draft['total'])}** ({draft['payment_method']})."
        f"{teks_hutang}",
        [*aksi_utama, *aksi_transaksi, "transaksi_atomik"],
    )


async def siapkan_record_payment(
    db: AsyncDatabase,
    session_id: str,
    pesan: str,
) -> tuple[str, list[str]]:
    """Validasi pembayaran hutang, simpan draft."""
    nama, jumlah = ekstrak_pembayaran_hutang(pesan)
    if not nama:
        return (
            "Hutang siapa yang dibayar? Contoh: \"Bu Sari bayar hutang 50 ribu\"",
            ["minta_nama_customer"],
        )
    if not jumlah or jumlah <= 0:
        return (
            "Jumlah pembayaran tidak valid. Contoh: \"bayar hutang 50 ribu\"",
            ["validasi_jumlah_gagal"],
        )

    customer, opsi = await _resolve_customer(db, nama)
    aksi = ["mcp:find"]

    if opsi:
        baris = "\n".join(f"  {i + 1}. {c['name']}" for i, c in enumerate(opsi))
        return f"Ada beberapa pelanggan yang cocok:\n{baris}", [*aksi, "disambiguasi_customer"]
    if not customer:
        return f"Customer \"{nama}\" tidak ditemukan.", [*aksi, "customer_tidak_ditemukan"]

    hutang = customer.get("debt_total", 0)
    if hutang <= 0:
        return f"{customer['name']} tidak punya hutang aktif.", aksi

    if jumlah > hutang:
        return (
            f"Pembayaran **{format_rupiah(jumlah)}** melebihi hutang "
            f"**{format_rupiah(hutang)}**. Tolong sesuaikan jumlahnya.",
            [*aksi, "jumlah_melebihi_hutang"],
        )

    draft = {
        "tipe": "record_payment",
        "customer_id": str(customer["_id"]),
        "customer_name": customer["name"],
        "amount": jumlah,
        "debt_before": hutang,
        "debt_after": hutang - jumlah,
    }
    await simpan_pending(db, session_id, draft)
    return format_ringkasan_pembayaran(draft), [*aksi, "minta_konfirmasi"]


async def eksekusi_record_payment(
    db: AsyncDatabase,
    session_id: str,
    draft: dict[str, Any],
) -> tuple[str, list[str]]:
    """Eksekusi pembayaran hutang setelah konfirmasi (transaksi atomik)."""
    sekarang = datetime.now(timezone.utc)
    aksi_utama = ["mcp:updateOne", "mcp:insertOne"]
    cid = ObjectId(draft["customer_id"])
    jumlah = draft["amount"]

    cust = await db.customers.find_one({"_id": cid})
    if not cust:
        await hapus_pending(db, session_id)
        return "Customer tidak ditemukan.", ["error"]

    sisa_bayar = jumlah
    riwayat_baru = []
    for entri in cust.get("debt_history", []):
        salinan = dict(entri)
        if not salinan.get("paid") and sisa_bayar > 0:
            if salinan["amount"] <= sisa_bayar:
                salinan["paid"] = True
                salinan["paid_date"] = sekarang
                sisa_bayar -= salinan["amount"]
            else:
                salinan["amount"] -= sisa_bayar
                sisa_bayar = 0
        riwayat_baru.append(salinan)

    async def _jalankan(sesi: AsyncClientSession) -> list[str]:
        aksi_dalam: list[str] = []
        _, aksi_upd = await mcp_update_one(
            db,
            "customers",
            {"_id": cid},
            {
                "$set": {
                    "debt_total": draft["debt_after"],
                    "debt_history": riwayat_baru,
                }
            },
            session=sesi,
        )
        aksi_dalam.extend(aksi_upd)

        _, aksi_ins = await mcp_insert_one(
            db,
            "transactions",
            {
                "type": "adjustment",
                "items": [],
                "total": jumlah,
                "payment_method": "tunai",
                "customer_id": cid,
                "notes": f"Pembayaran hutang {draft['customer_name']}",
                "created_at": sekarang,
            },
            session=sesi,
        )
        aksi_dalam.extend(aksi_ins)
        return aksi_dalam

    try:
        aksi_transaksi = await jalankan_dalam_transaksi(db, _jalankan)
    except Exception:
        return (
            "Gagal mencatat pembayaran — perubahan dibatalkan. Coba lagi sebentar.",
            ["error_transaksi_atomik"],
        )

    await hapus_pending(db, session_id)
    return (
        f"Pembayaran hutang **{draft['customer_name']}** "
        f"**{format_rupiah(jumlah)}** berhasil dicatat.\n"
        f"Sisa hutang: **{format_rupiah(draft['debt_after'])}**.",
        [*aksi_utama, *aksi_transaksi, "transaksi_atomik"],
    )
