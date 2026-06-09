"""Unit test lokalisasi EN — untuk judge."""

import pytest

from app.util.lokalisasi import konteks_bahasa, t


def test_t_bahasa_indonesia_default() -> None:
    assert t("Halo", "Hello") == "Halo"


def test_t_bahasa_inggris() -> None:
    with konteks_bahasa("en"):
        assert t("Halo", "Hello") == "Hello"


@pytest.mark.asyncio
async def test_check_stock_bahasa_inggris() -> None:
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.services.intent_handlers import handle_check_stock

    db = MagicMock()
    produk = {
        "name": "Indomie Goreng Original",
        "stock_current": 48,
        "stock_minimum": 10,
        "unit": "pcs",
    }

    with konteks_bahasa("en"):
        with patch(
            "app.services.intent_handlers.resolve_produk_tunggal",
            AsyncMock(return_value=(produk, None, ["mcp:find"])),
        ):
            balasan, _ = await handle_check_stock(
                db, "how much indomie goreng stock is left?"
            )

    assert "Stock" in balasan
    assert "OK" in balasan


def test_klasifikasi_english_revenue() -> None:
    from app.services.klasifikasi import klasifikasi_intent

    assert klasifikasi_intent("what is today's revenue?") == "sales_report"
