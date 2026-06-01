#!/usr/bin/env python3
"""Verifikasi Definition of Done Hari 3 — write intents + konfirmasi."""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
load_dotenv(ROOT / ".env")

GAGAL: list[str] = []


def _sid(label: str) -> str:
    return f"verifikasi-hari3-{label}-{uuid.uuid4().hex[:8]}"


def lolos(msg: str) -> None:
    print(f"  OK {msg}")


def gagal(msg: str) -> None:
    print(f"  GAGAL {msg}")
    GAGAL.append(msg)


async def main() -> None:
    from app.db.koneksi import dapatkan_database, tutup_koneksi
    from app.main import aplikasi
    from app.services.produk import cari_produk

    print("=== Verifikasi Hari 3 ===\n")
    db = await dapatkan_database()

    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://test", timeout=120.0) as klien:
        sid_sale = _sid("sale")
        print("[1] record_sale minta konfirmasi")
        r1 = await klien.post(
            "/api/chat",
            json={"pesan": "jual 1 indomie goreng"},
            headers={"X-Session-Id": sid_sale},
        )
        if r1.json().get("intent") != "record_sale" or "Konfirmasi" not in r1.json()["balasan"]:
            gagal("draft penjualan")
        else:
            lolos("draft penjualan")

        sesi = await db.agent_sessions.find_one({"session_id": sid_sale})
        if not sesi.get("context", {}).get("pending_write"):
            gagal("pending_write belum ada sebelum konfirmasi")
        else:
            lolos("pending_write tersimpan")

        sebelum, _ = await cari_produk(db, "indomie goreng", batas=1)
        stok_awal = sebelum[0]["stock_current"] if sebelum else 0

        print("\n[2] konfirmasi ya → write")
        r2 = await klien.post(
            "/api/chat",
            json={"pesan": "ya"},
            headers={"X-Session-Id": sid_sale},
        )
        if "berhasil dicatat" not in r2.json().get("balasan", "").lower():
            gagal("konfirmasi penjualan")
        else:
            lolos("penjualan dicatat")

        sesudah, _ = await cari_produk(db, "indomie goreng", batas=1)
        stok_akhir = sesudah[0]["stock_current"] if sesudah else 0
        if stok_akhir != stok_awal - 1:
            gagal(f"stok tidak berkurang: {stok_awal} -> {stok_akhir}")
        else:
            lolos(f"stok berkurang: {stok_awal} -> {stok_akhir}")

        tx = await db.transactions.find_one(
            {"type": "sale", "items.product_name": {"$regex": "Indomie Goreng", "$options": "i"}},
            sort=[("created_at", -1)],
        )
        if not tx:
            gagal("transaksi tidak ada di Atlas")
        else:
            lolos("transaksi sale di Atlas")

        print("\n[3] record_payment E2E")
        cust = await db.customers.find_one({"name": {"$regex": "^Bu Sari$", "$options": "i"}})
        if not cust or cust.get("debt_total", 0) < 5000:
            gagal("Bu Sari tidak punya hutang cukup untuk uji pembayaran")
        else:
            hutang_awal = cust["debt_total"]
            jumlah_bayar = min(5000, hutang_awal)
            sid_pay = _sid("pay")
            rp1 = await klien.post(
                "/api/chat",
                json={"pesan": f"Bu Sari bayar hutang {jumlah_bayar}"},
                headers={"X-Session-Id": sid_pay},
            )
            if rp1.json().get("intent") != "record_payment" or "Konfirmasi" not in rp1.json()["balasan"]:
                gagal("draft pembayaran")
            else:
                lolos("draft pembayaran hutang")

            rp2 = await klien.post(
                "/api/chat",
                json={"pesan": "ya"},
                headers={"X-Session-Id": sid_pay},
            )
            if "berhasil dicatat" not in rp2.json().get("balasan", "").lower():
                gagal("konfirmasi pembayaran")
            else:
                lolos("pembayaran dicatat")

            cust2 = await db.customers.find_one({"_id": cust["_id"]})
            hutang_akhir = cust2.get("debt_total", 0) if cust2 else hutang_awal
            if hutang_akhir != hutang_awal - jumlah_bayar:
                gagal(f"hutang tidak turun: {hutang_awal} -> {hutang_akhir}")
            else:
                lolos(f"hutang turun: {hutang_awal} -> {hutang_akhir}")

        print("\n[4] penjualan bon/hutang menambah hutang customer")
        cust3 = await db.customers.find_one({"name": {"$regex": "^Bu Sari$", "$options": "i"}})
        if not cust3:
            gagal("Bu Sari tidak ditemukan untuk uji bon")
        else:
            hutang_sebelum_bon = cust3.get("debt_total", 0)
            sid_bon = _sid("bon")
            rb1 = await klien.post(
                "/api/chat",
                json={"pesan": "jual 1 indomie goreng bon Bu Sari"},
                headers={"X-Session-Id": sid_bon},
            )
            if rb1.json().get("intent") != "record_sale" or "Konfirmasi" not in rb1.json()["balasan"]:
                gagal("draft penjualan bon")
            else:
                lolos("draft penjualan bon")

            rb2 = await klien.post(
                "/api/chat",
                json={"pesan": "ya"},
                headers={"X-Session-Id": sid_bon},
            )
            if "berhasil dicatat" not in rb2.json().get("balasan", "").lower():
                gagal("konfirmasi penjualan bon")
            else:
                lolos("penjualan bon dicatat")

            cust4 = await db.customers.find_one({"_id": cust3["_id"]})
            hutang_setelah = cust4.get("debt_total", 0) if cust4 else 0
            if cust4 and hutang_setelah <= hutang_sebelum_bon:
                gagal("hutang customer tidak bertambah setelah bon")
            else:
                lolos("hutang customer bertambah setelah bon")

        print("\n[5] debt_collection & sales_forecast")
        r3 = await klien.post(
            "/api/chat",
            json={"pesan": "siapa yang belum bayar hutang?"},
            headers={"X-Session-Id": _sid("dc")},
        )
        if r3.json().get("intent") != "debt_collection":
            gagal("debt_collection")
        else:
            lolos("debt_collection")

        r4 = await klien.post(
            "/api/chat",
            json={"pesan": "besok bakal ramai?"},
            headers={"X-Session-Id": _sid("fc")},
        )
        if r4.json().get("intent") != "sales_forecast":
            gagal("sales_forecast")
        else:
            lolos("sales_forecast")

        print("\n[6] draft baru menggantikan pending lama")
        sid_ganti = _sid("ganti")
        await klien.post(
            "/api/chat",
            json={"pesan": "jual 1 indomie goreng"},
            headers={"X-Session-Id": sid_ganti},
        )
        r_ganti = await klien.post(
            "/api/chat",
            json={"pesan": "jual 2 indomie goreng"},
            headers={"X-Session-Id": sid_ganti},
        )
        pending = (await db.agent_sessions.find_one({"session_id": sid_ganti}) or {}).get(
            "context", {}
        ).get("pending_write", {})
        qty_draft = pending.get("items", [{}])[0].get("qty") if pending.get("items") else 0
        if "Konfirmasi" not in r_ganti.json().get("balasan", "") or qty_draft != 2:
            gagal("draft baru tidak menggantikan pending lama")
        else:
            lolos("draft baru menggantikan pending")

    await tutup_koneksi()

    if GAGAL:
        print(f"\nGagal: {len(GAGAL)}")
        for g in GAGAL:
            print(f"  - {g}")
        sys.exit(1)
    print("\nSemua gate Hari 3 lolos.")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
