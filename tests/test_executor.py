"""Test retry executor saat Atlas error."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.executor import jalankan_dengan_retry, proses_pesan


@pytest.mark.asyncio
async def test_retry_satu_kali_lalu_sukses() -> None:
    """Handler gagal pertama kali, sukses di retry ke-2."""
    db = AsyncMock()
    panggilan = {"n": 0}

    async def handler_gagal_lalu_ok(db_arg, intent, pesan):
        panggilan["n"] += 1
        if panggilan["n"] == 1:
            raise ConnectionError("Atlas timeout simulasi")
        return "OK retry", ["mcp:find"]

    with patch("app.services.executor._jalankan_intent", side_effect=handler_gagal_lalu_ok):
        balasan, aksi = await jalankan_dengan_retry(db, "check_stock", "stok indomie")

    assert balasan == "OK retry"
    assert panggilan["n"] == 2


@pytest.mark.asyncio
async def test_retry_gagal_total() -> None:
    """Setelah 2 percobaan, error naik ke proses_pesan."""
    db = AsyncMock()

    async def selalu_gagal(db_arg, intent, pesan):
        raise RuntimeError("Atlas down")

    with patch("app.services.executor._jalankan_intent", side_effect=selalu_gagal):
        hasil = await proses_pesan(db, "stok indomie berapa?")

    assert "gangguan teknis" in hasil["balasan"].lower()
    assert "error_atlas" in hasil["actions_taken"]
