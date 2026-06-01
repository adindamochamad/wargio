"""Klasifikasi intent dari pesan Bahasa Indonesia."""

from __future__ import annotations

import re
from typing import Optional

INTENT_LIST = (
    "check_stock",
    "check_debt",
    "restock_alert",
    "sales_report",
    "unknown",
)

# Pola berurutan — intent spesifik dulu
POLA_INTENT: list[tuple[str, list[str]]] = [
    ("restock_alert", [
        r"mau habis", r"restock", r"perlu restock", r"stok kritis",
        r"produk apa yang", r"barang apa yang",
    ]),
    ("sales_report", [
        r"pendapatan", r"omzet", r"omset", r"penjualan hari",
        r"laporan penjualan", r"berapa jualan", r"total jual",
    ]),
    ("check_debt", [
        r"hutang", r"piutang", r"utang", r"belum bayar",
    ]),
    ("check_stock", [
        r"stok", r"stock", r"tinggal berapa", r"ada berapa",
        r"sisa berapa", r"masih ada",
    ]),
]


# Kata yang bukan nama produk — hasil ekstraksi invalid
KATA_BUKAN_PRODUK = frozenset({
    "berapa", "sisa", "tinggal", "ada", "masih", "min", "max",
})


def normalisasi_teks(pesan: str) -> str:
    """Lowercase dan bersihkan filler umum."""
    teks = pesan.lower().strip()
    for filler in ("bu", "pak", "mbak", "tolong", "dong", "deh", "ya"):
        teks = re.sub(rf"\b{filler}\b", " ", teks)
    return re.sub(r"\s+", " ", teks).strip()


def ekstrak_nama_produk(pesan: str) -> Optional[str]:
    """Ambil kata kunci produk setelah kata stok/stock."""
    teks = normalisasi_teks(pesan)
    for pola in (
        r"stok\s+(.+?)(?:\s+berapa|\?|$)",
        r"stock\s+(.+?)(?:\s+berapa|\?|$)",
        r"tinggal berapa\s+(.+?)(?:\?|$)",
        r"ada berapa\s+(.+?)(?:\?|$)",
    ):
        m = re.search(pola, teks)
        if m:
            nama = m.group(1).strip()
            if nama and nama not in KATA_BUKAN_PRODUK:
                return nama
    return None


def ekstrak_nama_customer(pesan: str) -> Optional[str]:
    """Ambil nama customer setelah kata hutang."""
    teks = normalisasi_teks(pesan)
    m = re.search(r"hutang\s+(.+?)(?:\?|$|total|berapa)", teks)
    if m:
        return m.group(1).strip()
    return None


def klasifikasi_intent(pesan: str) -> str:
    """Tentukan intent dari pesan user."""
    teks = normalisasi_teks(pesan)
    if not teks:
        return "unknown"

    for intent, pola_list in POLA_INTENT:
        for pola in pola_list:
            if re.search(pola, teks):
                return intent
    return "unknown"
