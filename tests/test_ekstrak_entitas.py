"""Test ekstraksi entitas — unit tanpa Atlas."""

from app.services.ekstrak_entitas import (
    ekstrak_item_penjualan,
    ekstrak_pembayaran_hutang,
)


def test_ekstrak_item_penjualan_english() -> None:
    item = ekstrak_item_penjualan(
        "sold 2 indomie goreng and 1 air mineral aqua 600ml",
    )
    assert len(item) == 2
    assert item[0] == (2, "indomie goreng")
    assert item[1] == (1, "air mineral aqua 600ml")


def test_ekstrak_pembayaran_english() -> None:
    nama, jumlah = ekstrak_pembayaran_hutang("Bu Sari paid debt 50000")
    assert nama == "bu sari"
    assert jumlah == 50000
