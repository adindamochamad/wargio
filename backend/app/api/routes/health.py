"""Health check — verifikasi API, Atlas, MCP, dan Gemini."""

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

    mcp_ok = False
    mcp_live = pengaturan.mcp_live_enabled
    if atlas_ok and mcp_live:
        from app.services.mcp_klien import cek_mcp_hidup

        mcp_ok = await cek_mcp_hidup()
    elif atlas_ok:
        mcp_ok = True

    from app.services.agent_gemini import gemini_runtime_ok
    gemini_ok = gemini_runtime_ok()
    gemini_aktif = pengaturan.gemini_terkonfigurasi and gemini_ok is not False

    return {
        "status": "ok",
        "service": "wargio-api",
        "atlas": atlas_ok,
        "atlas_configured": pengaturan.atlas_terkonfigurasi,
        "mcp": mcp_ok,
        "mcp_live_enabled": mcp_live,
        "mcp_mode": "live_stdio" if mcp_live else "pymongo_equivalent",
        "gemini_configured": pengaturan.gemini_terkonfigurasi,
        "gemini_available": gemini_ok,
        "agent_engine_id": pengaturan.agent_engine_id or None,
        "agent_engine_deployed": bool(pengaturan.agent_engine_id),
        "agent_mode": "gemini" if gemini_aktif else "intent_engine",
        "system_prompt": "backend/app/prompts/wargio_system.txt",
    }
