"""Test klasifikasi intent — unit tanpa Atlas."""

from app.services.klasifikasi import klasifikasi_intent, ekstrak_nama_produk


def test_klasifikasi_check_stock() -> None:
    assert klasifikasi_intent("stok mie instan berapa?") == "check_stock"


def test_klasifikasi_check_debt() -> None:
    assert klasifikasi_intent("hutang bu sari total berapa") == "check_debt"


def test_klasifikasi_restock_alert() -> None:
    assert klasifikasi_intent("produk apa yang mau habis?") == "restock_alert"


def test_klasifikasi_sales_report() -> None:
    assert klasifikasi_intent("pendapatan hari ini berapa?") == "sales_report"


def test_ekstrak_nama_produk() -> None:
    assert ekstrak_nama_produk("stok indomie goreng berapa?") == "indomie goreng"


def test_klasifikasi_unknown() -> None:
    assert klasifikasi_intent("") == "unknown"
