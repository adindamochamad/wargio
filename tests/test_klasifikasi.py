"""Test klasifikasi intent — unit tanpa Atlas."""

from app.services.klasifikasi import (
    ekstrak_nama_produk,
    klasifikasi_intent,
)


def test_klasifikasi_check_stock() -> None:
    assert klasifikasi_intent("stok mie instan berapa?") == "check_stock"


def test_klasifikasi_check_stock_variasi() -> None:
    assert klasifikasi_intent("Bu, tinggal berapa indomie?") == "check_stock"


def test_klasifikasi_check_debt() -> None:
    assert klasifikasi_intent("hutang bu sari total berapa") == "check_debt"


def test_klasifikasi_check_debt_variasi() -> None:
    assert klasifikasi_intent("piutang Pak Budi berapa?") == "check_debt"


def test_klasifikasi_restock_alert() -> None:
    assert klasifikasi_intent("produk apa yang mau habis?") == "restock_alert"


def test_klasifikasi_restock_alert_variasi() -> None:
    assert klasifikasi_intent("barang apa yang perlu restock?") == "restock_alert"


def test_klasifikasi_sales_report() -> None:
    assert klasifikasi_intent("pendapatan hari ini berapa?") == "sales_report"


def test_klasifikasi_sales_report_variasi() -> None:
    assert klasifikasi_intent("omzet minggu ini total berapa?") == "sales_report"


def test_ekstrak_nama_produk() -> None:
    assert ekstrak_nama_produk("stok indomie goreng berapa?") == "indomie goreng"


def test_ekstrak_nama_produk_tanpa_nama() -> None:
    """Bug fix: 'stok berapa?' tidak boleh jadi nama produk."""
    assert ekstrak_nama_produk("stok berapa?") is None


def test_klasifikasi_unknown() -> None:
    assert klasifikasi_intent("") == "unknown"


def test_klasifikasi_unknown_sapa() -> None:
    assert klasifikasi_intent("halo") == "unknown"
