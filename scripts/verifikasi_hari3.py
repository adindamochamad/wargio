#!/usr/bin/env python3
"""
Verifikasi Definition of Done Hari 3 — write intents + tier 2 dasar.
Exit 0 = lolos; 1 = ada blocker.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
load_dotenv(ROOT / ".env")

GAGAL: list[str] = []
LOLOS: list[str] = []


def catat_gagal(pesan: str) -> None:
    GAGAL.append(pesan)
    print(f"  GAGAL: {pesan}")


def catat_lolos(pesan: str) -> None:
    LOLOS.append(pesan)
    print(f"  OK: {pesan}")


def gate_modul_write() -> None:
    print("\n[GATE] Modul write intent")
    wajib = [
        BACKEND / "app" / "services" / "write_handlers.py",
        BACKEND / "app" / "services" / "konfirmasi.py",
        BACKEND / "app" / "services" / "transaksi_atomik.py",
    ]
    for path in wajib:
        if path.exists():
            catat_lolos(path.relative_to(ROOT).as_posix())
        else:
            catat_gagal(f"File hilang: {path.relative_to(ROOT)}")


def gate_klasifikasi_tier2() -> None:
    print("\n[GATE] Klasifikasi tier 2")
    from app.services.klasifikasi import klasifikasi_intent

    cek = [
        ("tadi jual 3 aqua", "record_sale"),
        ("Bu Sari bayar hutang 50 ribu", "record_payment"),
        ("siapa yang belum bayar hutang", "debt_collection"),
        ("besok bakal ramai ga?", "sales_forecast"),
    ]
    for pesan, harapan in cek:
        if klasifikasi_intent(pesan) == harapan:
            catat_lolos(f"{harapan} ← \"{pesan[:30]}...\"")
        else:
            catat_gagal(f"Intent {harapan} gagal untuk: {pesan}")


async def gate_stok_produk_uji() -> None:
    print("\n[GATE] Stok produk uji (Indomie Goreng)")
    from app.config import ambil_pengaturan
    from app.db.koneksi import dapatkan_database

    if not ambil_pengaturan().atlas_terkonfigurasi:
        catat_gagal("MONGODB_URI belum dikonfigurasi")
        return

    db = await dapatkan_database()
    produk = await db.products.find_one({"sku": "MKN-INDO-GORENG"})
    if not produk:
        catat_gagal("Produk MKN-INDO-GORENG tidak ada — jalankan seed_data.py")
        return
    if produk.get("stock_current", 0) < 5:
        catat_gagal(
            f"Stok indomie goreng={produk.get('stock_current')} — "
            "jalankan pytest test_hari3 (fixture reset) atau seed ulang"
        )
        return
    catat_lolos(f"Stok indomie goreng = {produk['stock_current']} pcs")


def gate_pytest_hari3() -> None:
    print("\n[GATE] pytest tests/test_hari3.py")
    py = ROOT / "backend" / ".venv" / "bin" / "python"
    if not py.exists():
        py = Path(sys.executable)
    hasil = subprocess.run(
        [str(py), "-m", "pytest", "tests/test_hari3.py", "-q", "--tb=no"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if hasil.returncode != 0:
        baris_gagal = [
            ln for ln in hasil.stdout.splitlines() if "FAILED" in ln or "failed" in ln
        ]
        ringkas = baris_gagal[-3:] if baris_gagal else [hasil.stdout[-300:]]
        catat_gagal(f"pytest hari3 gagal: {' | '.join(ringkas)}")
        return
    catat_lolos("Semua test Hari 3 lulus")


async def main() -> None:
    print("=== Verifikasi Hari 3 Wargio ===")
    gate_modul_write()
    gate_klasifikasi_tier2()
    await gate_stok_produk_uji()
    gate_pytest_hari3()

    print("\n=== Ringkasan ===")
    print(f"Lolos: {len(LOLOS)} | Gagal: {len(GAGAL)}")
    if GAGAL:
        for g in GAGAL:
            print(f"  - {g}")
        sys.exit(1)
    print("\nHari 3 Write + Tier 2: SEMUA GATE LOLOS.")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
