"""Test pipeline fuzzy matching produk."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import ambil_pengaturan
from app.main import aplikasi
from app.services.fuzzy_produk import (
    hitung_skor_partial,
    normalisasi_nama_produk,
    resolve_produk_fuzzy,
)

pytestmark = pytest.mark.skipif(
    not ambil_pengaturan().atlas_terkonfigurasi,
    reason="MONGODB_URI belum dikonfigurasi",
)


def test_normalisasi_nama_produk_hapus_filler() -> None:
    assert normalisasi_nama_produk("Bu, stok Indomie dong") == "stok indomie"


def test_skor_partial_exact() -> None:
    produk = {"name": "Indomie Goreng Original", "name_aliases": ["indomie goreng"]}
    assert hitung_skor_partial("indomie goreng", produk) == 1.0


def test_skor_partial_prefix() -> None:
    produk = {"name": "Indomie Goreng Original", "name_aliases": []}
    assert hitung_skor_partial("indomie", produk) == 0.8


def test_skor_partial_contains() -> None:
    produk = {"name": "Air Mineral Aqua 600ml", "name_aliases": []}
    assert hitung_skor_partial("aqua", produk) == 0.6


@pytest.mark.asyncio
async def test_resolve_indomie_goreng() -> None:
    from app.db.koneksi import dapatkan_database

    db = await dapatkan_database()
    produk, opsi, aksi = await resolve_produk_fuzzy(db, "indomie goreng")
    assert "fuzzy" in " ".join(aksi)
    assert produk is not None or len(opsi) >= 1
    if produk:
        assert "indomie" in produk["name"].lower()


@pytest.mark.asyncio
async def test_check_stock_capslock_via_api() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t", timeout=60.0) as klien:
        res = await klien.post(
            "/api/chat",
            json={"pesan": "STOK INDOMIE GORENG BERAPA?"},
            headers={"X-Session-Id": "test-fuzzy-caps"},
        )
    data = res.json()
    assert data["intent"] == "check_stock"
    assert "indomie" in data["balasan"].lower()
