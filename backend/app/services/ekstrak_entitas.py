"""Ekstraksi entitas dari pesan Bahasa Indonesia untuk intent Hari 3."""

from __future__ import annotations

import re
from typing import Optional

from app.services.klasifikasi import KATA_BUKAN_PRODUK, normalisasi_teks


def parse_jumlah_rupiah(teks: str) -> Optional[int]:
    """Parse angka Rupiah dari teks: 50 ribu, 50rb, 50000, Rp 50.000."""
    teks = teks.lower().replace(".", "").replace(",", "")
    m = re.search(r"rp\s*(\d+)", teks)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\s*(ribu|rb|jt|juta)", teks)
    if m:
        angka = int(m.group(1))
        satuan = m.group(2)
        if satuan in ("ribu", "rb"):
            return angka * 1000
        if satuan in ("jt", "juta"):
            return angka * 1_000_000
    m = re.search(r"\b(\d{4,})\b", teks)
    if m:
        return int(m.group(1))
    m = re.search(r"\b(\d{1,3})\s*(?:ribu|rb)\b", teks)
    if m:
        return int(m.group(1)) * 1000
    return None


def pisahkan_customer_dari_penjualan(pesan: str) -> tuple[str, Optional[str]]:
    """
    Pisahkan suffix customer untuk penjualan bon/hutang.
    Contoh: 'jual 2 indomie bon bu sari' → ('jual 2 indomie', 'bu sari').
    """
    # Jangan pakai normalisasi_teks — filler "bu/pak" adalah bagian nama customer
    teks = re.sub(r"\s+", " ", pesan.lower().strip())
    nama: Optional[str] = None
    pola_suffix = (
        r"\s+(?:bon|hutang|piutang)\s+(?:ke\s+)?(.+?)$",
        r"\s+ke\s+(.+?)\s+(?:bon|hutang|piutang)$",
    )
    for pola in pola_suffix:
        cocok = re.search(pola, teks)
        if cocok:
            nama = cocok.group(1).strip()
            teks = teks[: cocok.start()].strip()
            break
    return teks, nama


def ekstrak_item_penjualan(pesan: str) -> list[tuple[int, str]]:
    """
    Parse item penjualan: 'jual 3 aqua sama 2 rokok' → [(3, 'aqua'), (2, 'rokok')].
    """
    teks, _ = pisahkan_customer_dari_penjualan(pesan)
    teks = normalisasi_teks(teks)
    teks = re.sub(
        r"^(tadi\s+)?(jual|terjual|catat penjualan|catat jualan|jualan)\s+",
        "",
        teks,
    )
    if not teks:
        return []

    bagian = re.split(r"\s+(?:sama dengan|sama|dan|\+)\s+", teks)
    hasil: list[tuple[int, str]] = []
    for potong in bagian:
        potong = potong.strip().rstrip(".,!?")
        if not potong:
            continue
        cocok = re.match(r"^(\d+)\s+(.+)$", potong)
        if cocok:
            jumlah = int(cocok.group(1))
            nama = cocok.group(2).strip()
            nama = re.sub(r"\s+(?:bon|hutang|piutang)(?:\s+.*)?$", "", nama).strip()
            if jumlah > 0 and nama not in KATA_BUKAN_PRODUK:
                hasil.append((jumlah, nama))
    return hasil


def ekstrak_pembayaran_hutang(pesan: str) -> tuple[Optional[str], Optional[int]]:
    """
    Parse pembayaran hutang: nama customer + jumlah.
    Contoh: 'Bu Sari bayar hutang 50 ribu'
    """
    teks = normalisasi_teks(pesan)
    jumlah = parse_jumlah_rupiah(teks)

    # Pola: {nama} bayar hutang ...
    m = re.search(
        r"^(.+?)\s+bayar\s+(?:hutang|utang|piutang)",
        teks,
    )
    if m:
        return m.group(1).strip(), jumlah

    # Pola: bayar hutang {nama} ...
    m = re.search(
        r"bayar\s+(?:hutang|utang|piutang)\s+(.+?)(?:\s+\d|\s+rp|\s*$)",
        teks,
    )
    if m:
        nama = m.group(1).strip()
        # Buang sisa angka di nama jika ikut ter-parse
        nama = re.sub(r"\s+\d+.*$", "", nama).strip()
        return nama if nama else None, jumlah

    return None, jumlah


def ekstrak_nama_customer_umum(pesan: str) -> Optional[str]:
    """Ambil nama setelah kata customer/pelanggan."""
    teks = normalisasi_teks(pesan)
    m = re.search(r"(?:customer|pelanggan|pembeli)\s+(.+?)(?:\?|$)", teks)
    if m:
        return m.group(1).strip()
    return None
