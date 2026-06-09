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
async def test_check_stock_intent_indomie() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t", timeout=60.0) as klien:
        res = await klien.post(
            "/api/chat",
            json={"pesan": "stok indomie berapa?"},
            headers={"X-Session-Id": "test-check-stock-1"},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "check_stock"
    assert "Stok" in data["balasan"] or "stok" in data["balasan"].lower()


@pytest.mark.asyncio
async def test_check_stock_intent_aqua() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t", timeout=60.0) as klien:
        res = await klien.post(
            "/api/chat",
            json={"message": "stok aqua berapa?"},
            headers={"X-Session-Id": "test-check-stock-2"},
        )
    assert res.status_code == 200
    assert res.json()["intent"] == "check_stock"


@pytest.mark.asyncio
async def test_check_stock_produk_tidak_ditemukan() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t", timeout=60.0) as klien:
        res = await klien.post(
            "/api/chat",
            json={"pesan": "stok xyz999tidakada berapa?"},
            headers={"X-Session-Id": "test-check-stock-3"},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "check_stock"
    assert "tidak ditemukan" in data["balasan"].lower()


@pytest.mark.asyncio
async def test_check_stock_tanpa_nama_produk() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t", timeout=60.0) as klien:
        res = await klien.post(
            "/api/chat",
            json={"pesan": "stok berapa?"},
            headers={"X-Session-Id": "test-check-stock-4"},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "check_stock"
    assert "Produk mana" in data["balasan"]


@pytest.mark.asyncio
async def test_check_debt_intent_bu_sari() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t", timeout=60.0) as klien:
        res = await klien.post(
            "/api/chat",
            json={"pesan": "hutang Bu Sari berapa?"},
            headers={"X-Session-Id": "test-check-debt-1"},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "check_debt"
    assert "Hutang" in data["balasan"]


@pytest.mark.asyncio
async def test_check_debt_intent_pak_budi() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t", timeout=60.0) as klien:
        res = await klien.post(
            "/api/chat",
            json={"message": "hutang pak budi total berapa?"},
            headers={"X-Session-Id": "test-check-debt-2"},
        )
    assert res.status_code == 200
    assert res.json()["intent"] == "check_debt"


@pytest.mark.asyncio
async def test_check_debt_customer_tidak_ditemukan() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t", timeout=60.0) as klien:
        res = await klien.post(
            "/api/chat",
            json={"pesan": "hutang xyz999tidakada berapa?"},
            headers={"X-Session-Id": "test-check-debt-3"},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "check_debt"
    assert "tidak ditemukan" in data["balasan"].lower()


@pytest.mark.asyncio
async def test_restock_alert_intent_default() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t", timeout=60.0) as klien:
        res = await klien.post(
            "/api/chat",
            json={"pesan": "produk apa yang mau habis?"},
            headers={"X-Session-Id": "test-restock-1"},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "restock_alert"
    assert "restock" in data["balasan"].lower()


@pytest.mark.asyncio
async def test_restock_alert_variasi() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t", timeout=60.0) as klien:
        res = await klien.post(
            "/api/chat",
            json={"pesan": "stok kritis apa saja?"},
            headers={"X-Session-Id": "test-restock-2"},
        )
    assert res.status_code == 200
    assert res.json()["intent"] == "restock_alert"


@pytest.mark.asyncio
async def test_restock_alert_mengandung_produk() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t", timeout=60.0) as klien:
        res = await klien.post(
            "/api/chat",
            json={"pesan": "produk apa yang perlu restock?"},
            headers={"X-Session-Id": "test-restock-3"},
        )
    assert res.status_code == 200
    balasan = res.json()["balasan"]
    assert "Aqua" in balasan or "restock" in balasan.lower()


@pytest.mark.asyncio
async def test_sales_report_minggu_ini() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t", timeout=60.0) as klien:
        res = await klien.post(
            "/api/chat",
            json={"pesan": "pendapatan minggu ini berapa?"},
            headers={"X-Session-Id": "test-sales-1"},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "sales_report"
    assert "Pendapatan" in data["balasan"]


@pytest.mark.asyncio
async def test_sales_report_hari_ini() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t", timeout=60.0) as klien:
        res = await klien.post(
            "/api/chat",
            json={"message": "pendapatan hari ini berapa?"},
            headers={"X-Session-Id": "test-sales-2"},
        )
    assert res.status_code == 200
    assert res.json()["intent"] == "sales_report"


@pytest.mark.asyncio
async def test_sales_report_format_rupiah() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t", timeout=60.0) as klien:
        res = await klien.post(
            "/api/chat",
            json={"pesan": "omzet minggu ini berapa?"},
            headers={"X-Session-Id": "test-sales-3"},
        )
    assert res.status_code == 200
    assert "Rp" in res.json()["balasan"]


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


@pytest.mark.asyncio
async def test_health_menampilkan_agent_mode() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t") as klien:
        res = await klien.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["agent_mode"] in (
        "gemini",
        "intent_engine",
        "gemini_with_regex_fallback",
        "regex",
    )
    assert "mcp_tools" in data
    assert "mcp_mode" in data
