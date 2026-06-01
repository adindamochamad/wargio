"""Health check — verifikasi API dan koneksi Atlas."""

from fastapi import APIRouter

from app.config import ambil_pengaturan
from app.db.koneksi import cek_koneksi_atlas

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health_check() -> dict:
    """
    Status layanan. DoD Hari 1: harus return 200.
    Field `atlas` false jika URI belum diisi atau ping gagal.
    """
    pengaturan = ambil_pengaturan()
    atlas_ok = False
    if pengaturan.atlas_terkonfigurasi:
        atlas_ok = await cek_koneksi_atlas()

    return {
        "status": "ok",
        "service": "wargio-api",
        "atlas": atlas_ok,
        "atlas_configured": pengaturan.atlas_terkonfigurasi,
    }
