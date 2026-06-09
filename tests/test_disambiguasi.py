"""Test disambiguasi — unit tanpa Atlas."""

from app.services.disambiguasi import parse_pilihan_opsi
from app.services.fuzzy_produk import hitung_skor_partial


def test_parse_pilihan_angka() -> None:
    opsi = [{"name": "Air Mineral Aqua 600ml"}, {"name": "Air Mineral Aqua 1.5L"}]
    assert parse_pilihan_opsi("1", opsi) == 0
    assert parse_pilihan_opsi("2", opsi) == 1
    assert parse_pilihan_opsi("9", opsi) is None


def test_parse_pilihan_nama() -> None:
    opsi = [{"name": "Air Mineral Aqua 600ml"}, {"name": "Air Mineral Aqua 1.5L"}]
    assert parse_pilihan_opsi("air mineral aqua 600ml", opsi) == 0


def test_skor_partial_bonus_ukuran_600ml() -> None:
    aqua_600 = {"name": "Air Mineral Aqua 600ml", "name_aliases": []}
    aqua_15 = {"name": "Air Mineral Aqua 1.5L", "name_aliases": []}
    skor_600 = hitung_skor_partial("mineral aqua 600ml", aqua_600)
    skor_15 = hitung_skor_partial("mineral aqua 600ml", aqua_15)
    assert skor_600 >= 0.95
    assert skor_600 > skor_15
