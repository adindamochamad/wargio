"""
Unit test tambahan Hari 6 — tutup gap coverage tanpa Atlas live.
"""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId


# ---------------------------------------------------------------------------
# atlas_tools — cabang MCP live (mock)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mcp_find_live_fallback_ke_pymongo():
    from app.services import atlas_tools

    db = MagicMock()
    kursor = MagicMock()
    kursor.sort.return_value = kursor
    kursor.to_list = AsyncMock(return_value=[{"name": "Indomie", "stock_current": 5}])
    db.__getitem__.return_value.find.return_value = kursor

    pengaturan = MagicMock(mcp_live_enabled=True)
    with patch.object(atlas_tools, "ambil_pengaturan", return_value=pengaturan):
        with patch(
            "app.services.mcp_klien.panggil_mcp_find",
            side_effect=RuntimeError("MCP mati"),
        ):
            docs, aksi = await atlas_tools.mcp_find(db, "products", {"sku": "x"})

    assert docs[0]["name"] == "Indomie"
    assert "mcp:find:live_fallback" in aksi


@pytest.mark.asyncio
async def test_mcp_aggregate_live_fallback():
    from app.services import atlas_tools

    db = MagicMock()
    kursor = AsyncMock()
    kursor.to_list = AsyncMock(return_value=[{"total": 100}])
    koleksi = MagicMock()
    koleksi.aggregate = AsyncMock(return_value=kursor)
    db.__getitem__.return_value = koleksi

    pengaturan = MagicMock(mcp_live_enabled=True)
    with patch.object(atlas_tools, "ambil_pengaturan", return_value=pengaturan):
        with patch(
            "app.services.mcp_klien.panggil_mcp_aggregate",
            side_effect=RuntimeError("aggregate gagal"),
        ):
            hasil, aksi = await atlas_tools.mcp_aggregate(db, "transactions", [])

    assert hasil[0]["total"] == 100
    assert "mcp:aggregate:live_fallback" in aksi


@pytest.mark.asyncio
async def test_mcp_insert_one_live_fallback():
    from app.services import atlas_tools

    db = MagicMock()
    db.__getitem__.return_value.insert_one = AsyncMock(
        return_value=MagicMock(inserted_id="id1")
    )

    pengaturan = MagicMock(mcp_live_enabled=True)
    with patch.object(atlas_tools, "ambil_pengaturan", return_value=pengaturan):
        with patch(
            "app.services.mcp_klien.panggil_mcp_insert_one",
            side_effect=RuntimeError("insert gagal"),
        ):
            id_sisip, aksi = await atlas_tools.mcp_insert_one(
                db, "transactions", {"type": "sale"}
            )

    assert id_sisip == "id1"
    assert "mcp:insertOne:live_fallback" in aksi


@pytest.mark.asyncio
async def test_mcp_update_one_live_sukses():
    from app.services import atlas_tools

    db = MagicMock()
    db.__getitem__.return_value.update_one = AsyncMock(
        return_value=MagicMock(modified_count=1)
    )

    pengaturan = MagicMock(mcp_live_enabled=True)
    with patch.object(atlas_tools, "ambil_pengaturan", return_value=pengaturan):
        with patch("app.services.mcp_klien.panggil_mcp_update_one", AsyncMock()):
            jumlah, aksi = await atlas_tools.mcp_update_one(
                db, "products", {"sku": "a"}, {"$set": {"stock_current": 1}}
            )

    assert jumlah == 1
    assert "mcp:updateOne:live" in aksi


# ---------------------------------------------------------------------------
# mcp_klien — fungsi murni & pool disabled
# ---------------------------------------------------------------------------

def test_mcp_klien_parse_aggregate():
    from app.services.mcp_klien import parse_hasil_mcp_aggregate

    teks = '<untrusted-user-data-x>[{"total": 99}]</untrusted-user-data-x>'
    assert parse_hasil_mcp_aggregate(teks)[0]["total"] == 99


def test_mcp_klien_dokumen_ke_json():
    from app.services.mcp_klien import _dokumen_ke_json_mcp

    oid = ObjectId()
    hasil = _dokumen_ke_json_mcp({"_id": oid, "t": datetime(2026, 6, 9)})
    assert hasil["_id"] == {"$oid": str(oid)}
    assert "2026" in hasil["t"]


@pytest.mark.asyncio
async def test_mulai_pool_mcp_disabled():
    from app.services.mcp_klien import mulai_pool_mcp

    pengaturan = MagicMock(mcp_live_enabled=False)
    with patch("app.services.mcp_klien.ambil_pengaturan", return_value=pengaturan):
        assert await mulai_pool_mcp() is False


@pytest.mark.asyncio
async def test_tutup_pool_mcp_tanpa_stack():
    from app.services import mcp_klien

    mcp_klien._stack = None
    mcp_klien._sesi = None
    await mcp_klien.tutup_pool_mcp()


# ---------------------------------------------------------------------------
# embed_produk & agent_gemini
# ---------------------------------------------------------------------------

def test_teks_untuk_embedding_produk_alias():
    from app.services.embed_produk import teks_untuk_embedding_produk

    teks = teks_untuk_embedding_produk("Indomie", ["indomie goreng", "indomie"])
    assert "Indomie" in teks
    assert "indomie goreng" in teks


@pytest.mark.asyncio
async def test_buat_embedding_teks_kosong():
    from app.services.embed_produk import buat_embedding_teks

    assert await buat_embedding_teks("   ") is None


@pytest.mark.asyncio
async def test_klasifikasi_gemini_mock_sukses():
    from app.services import agent_gemini

    agent_gemini._gemini_status.update({"ok": None, "error": None})
    klien_palsu = MagicMock()
    klien_palsu.models.generate_content.return_value = MagicMock(text="check_stock")

    pengaturan = MagicMock(gemini_terkonfigurasi=True, gemini_model="gemini-2.5-flash")
    with patch.object(agent_gemini, "ambil_pengaturan", return_value=pengaturan):
        with patch.object(agent_gemini, "_buat_klien_gemini", return_value=klien_palsu):
            hasil = await agent_gemini.klasifikasi_dengan_gemini("stok indomie berapa?")

    assert hasil == "check_stock"
    assert agent_gemini.gemini_runtime_ok() is True


@pytest.mark.asyncio
async def test_klasifikasi_gemini_tidak_terkonfigurasi():
    from app.services import agent_gemini

    pengaturan = MagicMock(gemini_terkonfigurasi=False)
    with patch.object(agent_gemini, "ambil_pengaturan", return_value=pengaturan):
        assert await agent_gemini.klasifikasi_dengan_gemini("halo") is None


# ---------------------------------------------------------------------------
# main — CORS default
# ---------------------------------------------------------------------------

def test_daftar_asal_cors_kosong_default_localhost():
    from app.main import _daftar_asal_cors

    pengaturan = MagicMock(cors_origins="")
    with patch("app.main.ambil_pengaturan", return_value=pengaturan):
        assert _daftar_asal_cors() == ["http://localhost:3000"]
