"""Test intent Hari 3 — write + tier 2."""

import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import ambil_pengaturan
from app.main import aplikasi
from app.services.ekstrak_entitas import (
    ekstrak_item_penjualan,
    parse_jumlah_rupiah,
    pisahkan_customer_dari_penjualan,
)
from app.services.klasifikasi import klasifikasi_intent

pytestmark = pytest.mark.skipif(
    not ambil_pengaturan().atlas_terkonfigurasi,
    reason="MONGODB_URI belum dikonfigurasi",
)

# Produk uji penjualan — stok di-reset agar test tidak gagal setelah run sebelumnya
SKU_PRODUK_UJI = "MKN-INDO-GORENG"
STOK_UJI = 50


@pytest.fixture(autouse=True)
async def siapkan_stok_produk_uji() -> None:
    """Pastikan Indomie Goreng punya stok cukup untuk skenario record_sale."""
    from app.db.koneksi import dapatkan_database

    db = await dapatkan_database()
    await db.products.update_one(
        {"sku": SKU_PRODUK_UJI},
        {
            "$set": {
                "stock_current": STOK_UJI,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )


def test_klasifikasi_record_sale() -> None:
    assert klasifikasi_intent("tadi jual 3 aqua") == "record_sale"


def test_klasifikasi_record_payment() -> None:
    assert klasifikasi_intent("Bu Sari bayar hutang 50 ribu") == "record_payment"


def test_klasifikasi_debt_collection() -> None:
    assert klasifikasi_intent("siapa yang belum bayar hutang") == "debt_collection"


def test_klasifikasi_sales_forecast() -> None:
    assert klasifikasi_intent("besok bakal ramai ga?") == "sales_forecast"


def test_parse_jumlah_rupiah() -> None:
    assert parse_jumlah_rupiah("50 ribu") == 50000
    assert parse_jumlah_rupiah("100rb") == 100000


def test_ekstrak_item_penjualan() -> None:
    item = ekstrak_item_penjualan("jual 3 aqua sama 2 indomie")
    assert len(item) == 2
    assert item[0] == (3, "aqua")


def test_ekstrak_item_penjualan_minus() -> None:
    item = ekstrak_item_penjualan("jual minus 2 indomie")
    assert item == [(-2, "indomie")]


def test_ekstrak_item_penjualan_nol() -> None:
    item = ekstrak_item_penjualan("jual nol indomie")
    assert item == [(0, "indomie")]


def test_ekstrak_item_penjualan_angka_nol() -> None:
    item = ekstrak_item_penjualan("jual 0 indomie")
    assert item == [(0, "indomie")]


def test_pisahkan_customer_bon() -> None:
    teks, nama = pisahkan_customer_dari_penjualan("jual 2 indomie bon bu sari")
    assert "bon" not in teks
    assert nama == "bu sari"
    item = ekstrak_item_penjualan("jual 2 indomie bon bu sari")
    assert item[0] == (2, "indomie")


def _session_id_unik(prefix: str) -> str:
    """ID sesi baru agar tidak bentrok dengan data Atlas dari run sebelumnya."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


@pytest.mark.asyncio
async def test_record_sale_butuh_konfirmasi() -> None:
    transport = ASGITransport(app=aplikasi)
    sid = _session_id_unik("hari3-sale-draft")
    async with AsyncClient(transport=transport, base_url="http://t", timeout=90.0) as klien:
        res = await klien.post(
            "/api/chat",
            json={"pesan": "jual 1 indomie goreng"},
            headers={"X-Session-Id": sid},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["intent"] == "record_sale"
    assert "Konfirmasi" in data["balasan"]


@pytest.mark.asyncio
async def test_record_sale_tanpa_konfirmasi_tidak_write() -> None:
    from app.db.koneksi import dapatkan_database

    transport = ASGITransport(app=aplikasi)
    sid = _session_id_unik("hari3-no-write")
    async with AsyncClient(transport=transport, base_url="http://t", timeout=90.0) as klien:
        await klien.post(
            "/api/chat",
            json={"pesan": "jual 1 indomie goreng"},
            headers={"X-Session-Id": sid},
        )
    db = await dapatkan_database()
    sesi = await db.agent_sessions.find_one({"session_id": sid})
    assert sesi.get("context", {}).get("pending_write")


@pytest.mark.asyncio
async def test_flow_record_sale_lalu_cek_stok() -> None:
    """DoD Hari 3: record_sale -> konfirmasi -> check_stock stok berkurang."""
    from app.db.koneksi import dapatkan_database
    from app.services.produk import cari_produk

    transport = ASGITransport(app=aplikasi)
    sid = _session_id_unik("hari3-flow-sale")
    async with AsyncClient(transport=transport, base_url="http://t", timeout=120.0) as klien:
        db = await dapatkan_database()
        sebelum, _ = await cari_produk(db, "indomie goreng", batas=1)
        stok_awal = sebelum[0]["stock_current"] if sebelum else 0

        r1 = await klien.post(
            "/api/chat",
            json={"pesan": "jual 2 indomie goreng"},
            headers={"X-Session-Id": sid},
        )
        assert "Konfirmasi" in r1.json()["balasan"]

        r2 = await klien.post(
            "/api/chat",
            json={"pesan": "ya"},
            headers={"X-Session-Id": sid},
        )
        assert "berhasil dicatat" in r2.json()["balasan"].lower()

        r3 = await klien.post(
            "/api/chat",
            json={"pesan": "stok indomie goreng berapa?"},
            headers={"X-Session-Id": sid},
        )
        balasan = r3.json()["balasan"]
        sesudah, _ = await cari_produk(db, "indomie goreng", batas=1)
        stok_akhir = sesudah[0]["stock_current"] if sesudah else 0

    assert stok_akhir == stok_awal - 2
    assert "Stok" in balasan


@pytest.mark.asyncio
async def test_qty_negatif_ditolak() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t", timeout=90.0) as klien:
        res = await klien.post(
            "/api/chat",
            json={"pesan": "jual minus 2 indomie goreng"},
            headers={"X-Session-Id": _session_id_unik("hari3-qty-neg")},
        )
    balasan = res.json()["balasan"].lower()
    assert "tidak valid" in balasan


@pytest.mark.asyncio
async def test_qty_nol_ditolak() -> None:
    transport = ASGITransport(app=aplikasi)
    for pesan in ("jual 0 indomie goreng", "jual nol indomie goreng"):
        async with AsyncClient(transport=transport, base_url="http://t", timeout=90.0) as klien:
            res = await klien.post(
                "/api/chat",
                json={"pesan": pesan},
                headers={"X-Session-Id": _session_id_unik("hari3-qty-nol")},
            )
        assert "tidak valid" in res.json()["balasan"].lower()


@pytest.mark.asyncio
async def test_konfirmasi_stok_berubah_ditolak() -> None:
    """Stok habis antara draft dan konfirmasi — tidak boleh write."""
    from app.db.koneksi import dapatkan_database

    transport = ASGITransport(app=aplikasi)
    sid = _session_id_unik("hari3-stok-race")
    db = await dapatkan_database()
    await db.products.update_one(
        {"sku": SKU_PRODUK_UJI},
        {"$set": {"stock_current": 1}},
    )

    async with AsyncClient(transport=transport, base_url="http://t", timeout=90.0) as klien:
        r1 = await klien.post(
            "/api/chat",
            json={"pesan": "jual 1 indomie goreng"},
            headers={"X-Session-Id": sid},
        )
        assert "Konfirmasi" in r1.json()["balasan"]

        await db.products.update_one(
            {"sku": SKU_PRODUK_UJI},
            {"$set": {"stock_current": 0}},
        )

        r2 = await klien.post(
            "/api/chat",
            json={"pesan": "ya"},
            headers={"X-Session-Id": sid},
        )

    balasan = r2.json()["balasan"].lower()
    assert "tidak cukup" in balasan
    assert "berhasil dicatat" not in balasan

    sesi = await db.agent_sessions.find_one({"session_id": sid})
    assert sesi.get("context", {}).get("pending_write") is None


@pytest.mark.asyncio
async def test_stok_tidak_cukup_ditolak() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t", timeout=90.0) as klien:
        res = await klien.post(
            "/api/chat",
            json={"pesan": "jual 99999 indomie goreng"},
            headers={"X-Session-Id": "test-hari3-stok-gagal"},
        )
    assert "tidak cukup" in res.json()["balasan"].lower()


@pytest.mark.asyncio
async def test_flow_record_payment() -> None:
    """E2E: record_payment → konfirmasi → hutang turun."""
    from app.db.koneksi import dapatkan_database

    db = await dapatkan_database()
    cust = await db.customers.find_one({"name": {"$regex": "Bu Sari", "$options": "i"}})
    if not cust or cust.get("debt_total", 0) < 1000:
        pytest.skip("Bu Sari tanpa hutang di seed")

    hutang_awal = cust["debt_total"]
    jumlah = min(1000, hutang_awal)
    transport = ASGITransport(app=aplikasi)
    sid = _session_id_unik("hari3-payment")
    async with AsyncClient(transport=transport, base_url="http://t", timeout=120.0) as klien:
        r1 = await klien.post(
            "/api/chat",
            json={"pesan": f"Bu Sari bayar hutang {jumlah}"},
            headers={"X-Session-Id": sid},
        )
        assert r1.json()["intent"] == "record_payment"
        assert "Konfirmasi" in r1.json()["balasan"]

        r2 = await klien.post(
            "/api/chat",
            json={"pesan": "ya"},
            headers={"X-Session-Id": sid},
        )
        assert "berhasil dicatat" in r2.json()["balasan"].lower()

    cust2 = await db.customers.find_one({"_id": cust["_id"]})
    assert cust2["debt_total"] == hutang_awal - jumlah


@pytest.mark.asyncio
async def test_draft_baru_ganti_pending() -> None:
    """Pesan record_sale baru menggantikan draft lama di sesi yang sama."""
    from app.db.koneksi import dapatkan_database

    transport = ASGITransport(app=aplikasi)
    sid = _session_id_unik("hari3-ganti-draft")
    async with AsyncClient(transport=transport, base_url="http://t", timeout=120.0) as klien:
        await klien.post(
            "/api/chat",
            json={"pesan": "jual 1 indomie goreng"},
            headers={"X-Session-Id": sid},
        )
        await klien.post(
            "/api/chat",
            json={"pesan": "jual 3 indomie goreng"},
            headers={"X-Session-Id": sid},
        )
    db = await dapatkan_database()
    pending = (
        await db.agent_sessions.find_one({"session_id": sid})
    ).get("context", {}).get("pending_write", {})
    assert pending.get("items", [{}])[0].get("qty") == 3


@pytest.mark.asyncio
async def test_debt_collection_intent() -> None:
    transport = ASGITransport(app=aplikasi)
    async with AsyncClient(transport=transport, base_url="http://t", timeout=90.0) as klien:
        res = await klien.post(
            "/api/chat",
            json={"pesan": "siapa yang belum bayar hutang?"},
            headers={"X-Session-Id": "test-hari3-debt-coll"},
        )
    data = res.json()
    assert data["intent"] == "debt_collection"
    assert "Hutang" in data["balasan"] or "hutang" in data["balasan"].lower()
