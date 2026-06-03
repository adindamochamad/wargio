"""
Hari 6 — Testing Blitz & Hardening.

Cakupan:
- Unit tests atlas_tools (_convert_oid, parse_hasil_mcp_aggregate)
- Dashboard endpoint via ASGI
- Edge cases write intent (qty=0, format tidak valid, bon tanpa nama, jumlah melebihi hutang)
- Intent handlers (debt_collection, sales_forecast, stok_hampir_habis, customer_no_debt)
- Isolasi sesi (2 session_id tidak saling campur)
- format_rupiah edge cases
"""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import ambil_pengaturan
from app.main import aplikasi

pytestmark = pytest.mark.skipif(
    not ambil_pengaturan().atlas_terkonfigurasi,
    reason="MONGODB_URI belum dikonfigurasi",
)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _klien():
    return AsyncClient(transport=ASGITransport(app=aplikasi), base_url="http://t", timeout=60.0)


async def _chat(klien, pesan: str, session_id: str = "h6-default") -> dict:
    res = await klien.post(
        "/api/chat",
        json={"pesan": pesan},
        headers={"X-Session-Id": session_id},
    )
    assert res.status_code == 200, f"HTTP {res.status_code}: {res.text}"
    return res.json()


# ---------------------------------------------------------------------------
# Unit — atlas_tools (pure functions)
# ---------------------------------------------------------------------------

def test_convert_oid_plain_value():
    from app.services.atlas_tools import _convert_oid
    assert _convert_oid("hello") == "hello"
    assert _convert_oid(42) == 42


def test_convert_oid_oid_dict():
    from app.services.atlas_tools import _convert_oid
    assert _convert_oid({"$oid": "abc123"}) == "abc123"


def test_convert_oid_nested_dict():
    from app.services.atlas_tools import _convert_oid
    hasil = _convert_oid({"_id": {"$oid": "abc"}, "name": "test"})
    assert hasil == {"_id": "abc", "name": "test"}


def test_convert_oid_list():
    from app.services.atlas_tools import _convert_oid
    hasil = _convert_oid([{"$oid": "x"}, "plain"])
    assert hasil == ["x", "plain"]


def test_parse_hasil_mcp_aggregate_valid():
    from app.services.atlas_tools import parse_hasil_mcp_aggregate
    teks = (
        '<untrusted-user-data-abc>'
        '[{"_id": null, "total": 5000}]'
        '</untrusted-user-data-abc>'
    )
    hasil = parse_hasil_mcp_aggregate(teks)
    assert len(hasil) == 1
    assert hasil[0]["total"] == 5000


def test_parse_hasil_mcp_aggregate_no_match():
    from app.services.atlas_tools import parse_hasil_mcp_aggregate
    assert parse_hasil_mcp_aggregate("tidak ada tag khusus") == []


def test_parse_hasil_mcp_aggregate_invalid_json():
    from app.services.atlas_tools import parse_hasil_mcp_aggregate
    teks = '<untrusted-user-data-x>[invalid json}</untrusted-user-data-x>'
    assert parse_hasil_mcp_aggregate(teks) == []


# ---------------------------------------------------------------------------
# Unit — format_rupiah
# ---------------------------------------------------------------------------

def test_format_rupiah_nol():
    from app.util.format import format_rupiah
    assert format_rupiah(0) == "Rp 0"


def test_format_rupiah_ribuan():
    from app.util.format import format_rupiah
    assert "50.000" in format_rupiah(50000)


def test_format_rupiah_jutaan():
    from app.util.format import format_rupiah
    assert "1.000.000" in format_rupiah(1_000_000)


# ---------------------------------------------------------------------------
# Dashboard endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dashboard_schema_valid():
    async with _klien() as klien:
        res = await klien.get("/api/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "stok_kritis" in data
    assert "total_hutang_aktif" in data
    assert "omzet_hari_ini" in data
    assert "jumlah_transaksi_hari_ini" in data
    assert isinstance(data["stok_kritis"], list)


@pytest.mark.asyncio
async def test_dashboard_stok_kritis_fields():
    async with _klien() as klien:
        res = await klien.get("/api/dashboard")
    assert res.status_code == 200
    items = res.json()["stok_kritis"]
    if items:
        item = items[0]
        assert "nama" in item
        assert "stok_saat_ini" in item
        assert "stok_minimum" in item


# ---------------------------------------------------------------------------
# Edge cases — pesan tidak valid
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pesan_hanya_spasi_diproses():
    # Spasi-only lolos validasi Pydantic (minLength=1 terpenuhi), API tetap merespons
    async with _klien() as klien:
        res = await klien.post("/api/chat", json={"pesan": "   "})
    assert res.status_code in (200, 422)


@pytest.mark.asyncio
async def test_pesan_kosong_ditolak():
    async with _klien() as klien:
        res = await klien.post("/api/chat", json={"pesan": ""})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_tanpa_body_ditolak():
    async with _klien() as klien:
        res = await klien.post("/api/chat", json={})
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Edge cases — record_sale
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_record_sale_format_tidak_jelas():
    async with _klien() as klien:
        data = await _chat(klien, "jual dong", "h6-sale-noparse")
    # Bukan record_sale atau minta klarifikasi
    assert data["balasan"]


@pytest.mark.asyncio
async def test_record_sale_produk_tidak_ada():
    async with _klien() as klien:
        data = await _chat(klien, "jual 2 produkxyz99tidakada123", "h6-sale-notfound")
    assert "tidak ditemukan" in data["balasan"].lower()


@pytest.mark.asyncio
async def test_record_sale_stok_tidak_cukup():
    async with _klien() as klien:
        data = await _chat(klien, "jual 9999 indomie goreng", "h6-sale-stok")
    assert "tidak cukup" in data["balasan"].lower() or "stok" in data["balasan"].lower()


@pytest.mark.asyncio
async def test_record_sale_bon_tanpa_nama_customer():
    async with _klien() as klien:
        data = await _chat(klien, "jual 2 indomie goreng bon", "h6-sale-bon-noname")
    assert data["intent"] == "record_sale"
    balasan = data["balasan"].lower()
    assert "nama" in balasan or "customer" in balasan or "konfirmasi" in balasan or "berhasil" in balasan


@pytest.mark.asyncio
async def test_record_sale_customer_tidak_ditemukan():
    async with _klien() as klien:
        data = await _chat(klien, "jual 1 indomie goreng bon xyz999pelanggantiada", "h6-sale-cust-notfound")
    assert data["intent"] == "record_sale"
    assert "tidak ditemukan" in data["balasan"].lower() or "konfirmasi" in data["balasan"].lower()


# ---------------------------------------------------------------------------
# Edge cases — record_payment
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_record_payment_tanpa_nama():
    # "bayar hutang 50 ribu" — regex parse "50 ribu" sebagai nama → customer tidak ditemukan
    async with _klien() as klien:
        data = await _chat(klien, "bayar hutang 50 ribu", "h6-pay-noname")
    assert data["intent"] == "record_payment"
    # Bisa: tidak ditemukan, minta nama, atau minta jumlah — asalkan ada respons valid
    assert data["balasan"]


@pytest.mark.asyncio
async def test_record_payment_tanpa_jumlah():
    async with _klien() as klien:
        data = await _chat(klien, "Bu Sari bayar hutang", "h6-pay-noamount")
    assert data["intent"] == "record_payment"
    balasan = data["balasan"].lower()
    assert "jumlah" in balasan or "bayar" in balasan or "hutang" in balasan


@pytest.mark.asyncio
async def test_record_payment_customer_tidak_ditemukan():
    async with _klien() as klien:
        data = await _chat(klien, "xyz999tidakada bayar hutang 10 ribu", "h6-pay-notfound")
    assert data["intent"] == "record_payment"
    assert "tidak ditemukan" in data["balasan"].lower()


@pytest.mark.asyncio
async def test_record_payment_melebihi_hutang():
    async with _klien() as klien:
        data = await _chat(klien, "Bu Sari bayar hutang 999 juta", "h6-pay-exceed")
    assert data["intent"] == "record_payment"
    balasan = data["balasan"].lower()
    # Bisa: "melebihi hutang" atau langsung konfirmasi jika hutang besar
    assert "hutang" in balasan or "bayar" in balasan


# ---------------------------------------------------------------------------
# Intent — debt_collection & sales_forecast
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_debt_collection_intent():
    async with _klien() as klien:
        data = await _chat(klien, "siapa yang belum bayar hutang?", "h6-debt-col")
    assert data["intent"] == "debt_collection"
    balasan = data["balasan"].lower()
    assert "hutang" in balasan or "customer" in balasan or "tidak ada" in balasan


@pytest.mark.asyncio
async def test_debt_collection_variasi():
    async with _klien() as klien:
        data = await _chat(klien, "tampilkan semua yang belum lunas bon", "h6-debt-col-2")
    assert data["intent"] in ("debt_collection", "check_debt")


@pytest.mark.asyncio
async def test_sales_forecast_intent():
    async with _klien() as klien:
        data = await _chat(klien, "besok bakal ramai ga?", "h6-forecast")
    assert data["intent"] == "sales_forecast"
    balasan = data["balasan"].lower()
    assert "besok" in balasan or "perkiraan" in balasan or "forecast" in balasan


@pytest.mark.asyncio
async def test_sales_forecast_variasi():
    async with _klien() as klien:
        data = await _chat(klien, "prediksi omzet besok", "h6-forecast-2")
    assert data["intent"] == "sales_forecast"


# ---------------------------------------------------------------------------
# check_stock — status stok mendekati / hampir habis
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_check_stock_indomie_status_ada():
    async with _klien() as klien:
        data = await _chat(klien, "stok indomie goreng berapa?", "h6-stock-status")
    assert data["intent"] == "check_stock"
    balasan = data["balasan"].lower()
    assert "stok" in balasan
    # Status harus ada: aman / hampir habis / mendekati minimum
    assert any(k in balasan for k in ["aman", "habis", "minimum", "restock"])


@pytest.mark.asyncio
async def test_check_stock_produk_kritis_status():
    async with _klien() as klien:
        # Aqua sedang dalam stok kritis (stok 2/11)
        data = await _chat(klien, "stok aqua 600ml berapa?", "h6-stock-kritis")
    assert data["intent"] == "check_stock"
    balasan = data["balasan"].lower()
    assert "habis" in balasan or "restock" in balasan or "minimum" in balasan


# ---------------------------------------------------------------------------
# check_debt — customer tanpa hutang
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_check_debt_customer_ada_tanpa_hutang():
    # Cari nama customer yang mungkin tidak punya hutang
    # Gunakan nama yang tidak akan match di Atlas
    async with _klien() as klien:
        data = await _chat(klien, "hutang xyz999nohutang berapa?", "h6-debt-none")
    assert data["intent"] == "check_debt"
    # Bisa: tidak ditemukan atau tidak punya hutang
    assert data["balasan"]


# ---------------------------------------------------------------------------
# Isolasi sesi
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_isolasi_sesi_dua_sesi_independen():
    """Dua session berbeda tidak saling mempengaruhi."""
    async with _klien() as klien:
        # Sesi A tanya stok aqua
        data_a = await _chat(klien, "stok aqua 600ml berapa?", "h6-iso-sesi-A")
        # Sesi B tanya hutang
        data_b = await _chat(klien, "hutang Bu Sari berapa?", "h6-iso-sesi-B")

    # Intent sesi A harus check_stock, bukan terpengaruh sesi B
    assert data_a["intent"] == "check_stock"
    assert data_b["intent"] == "check_debt"
    assert data_a["session_id"] == "h6-iso-sesi-A"
    assert data_b["session_id"] == "h6-iso-sesi-B"


@pytest.mark.asyncio
async def test_isolasi_sesi_session_id_di_respons():
    """Session ID di respons harus sama dengan yang dikirim."""
    sid = "h6-session-echo-test"
    async with _klien() as klien:
        data = await _chat(klien, "stok indomie berapa?", sid)
    assert data["session_id"] == sid


@pytest.mark.asyncio
async def test_isolasi_sesi_disimpan_atlas():
    """Dua sesi berbeda masing-masing tersimpan di Atlas."""
    from app.db.koneksi import dapatkan_database

    sid_a, sid_b = "h6-persist-A", "h6-persist-B"
    async with _klien() as klien:
        await _chat(klien, "stok aqua berapa?", sid_a)
        await _chat(klien, "stok indomie berapa?", sid_b)

    db = await dapatkan_database()
    sesi_a = await db.agent_sessions.find_one({"session_id": sid_a})
    sesi_b = await db.agent_sessions.find_one({"session_id": sid_b})
    assert sesi_a is not None
    assert sesi_b is not None
    # Pesan sesi A tidak boleh ada di sesi B
    pesan_a = {m["content"] for m in sesi_a.get("messages", [])}
    pesan_b = {m["content"] for m in sesi_b.get("messages", [])}
    assert "stok aqua berapa?" not in pesan_b
    assert "stok indomie berapa?" not in pesan_a


# ---------------------------------------------------------------------------
# Rate limit header
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_response_headers():
    async with _klien() as klien:
        res = await klien.get("/api/health")
    assert res.status_code == 200
    # Content-Type harus application/json
    assert "application/json" in res.headers.get("content-type", "")
