"""Test intent Hari 2 — integrasi dengan Atlas."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import ambil_pengaturan
from app.main import aplikasi

pytestmark = pytest.mark.skipif(
    not ambil_pengaturan().atlas_terkonfigurasi,
    reason="MONGODB_URI belum dikonfigurasi",
)


@pytest.mark.asyncio
async def test_check_stock_intent() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t", timeout=60.0) as klien:
        res = await klien.post(
            "/api/chat",
            json={"pesan": "stok indomie berapa?"},
            headers={"X-Session-Id": "test-check-stock"},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "check_stock"
    assert "Stok" in data["balasan"] or "stok" in data["balasan"].lower()


@pytest.mark.asyncio
async def test_check_debt_intent() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t", timeout=60.0) as klien:
        res = await klien.post(
            "/api/chat",
            json={"pesan": "hutang Bu Sari berapa?"},
            headers={"X-Session-Id": "test-check-debt"},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "check_debt"


@pytest.mark.asyncio
async def test_restock_alert_intent() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t", timeout=60.0) as klien:
        res = await klien.post(
            "/api/chat",
            json={"pesan": "produk apa yang mau habis?"},
            headers={"X-Session-Id": "test-restock"},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "restock_alert"


@pytest.mark.asyncio
async def test_sales_report_intent() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t", timeout=60.0) as klien:
        res = await klien.post(
            "/api/chat",
            json={"pesan": "pendapatan minggu ini berapa?"},
            headers={"X-Session-Id": "test-sales-report"},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "sales_report"


@pytest.mark.asyncio
async def test_sesi_disimpan_di_atlas() -> None:
    from app.db.koneksi import dapatkan_database

    session_id = "test-sesi-persist"
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t", timeout=60.0) as klien:
        await klien.post(
            "/api/chat",
            json={"pesan": "stok aqua berapa?"},
            headers={"X-Session-Id": session_id},
        )
    db = await dapatkan_database()
    sesi = await db.agent_sessions.find_one({"session_id": session_id})
    assert sesi is not None
    assert len(sesi.get("messages", [])) >= 2


@pytest.mark.asyncio
async def test_pesan_kosong_ditolak() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t") as klien:
        res = await klien.post("/api/chat", json={"pesan": ""})
    assert res.status_code == 422
