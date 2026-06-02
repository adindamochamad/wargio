"""Dashboard mini — data ringkas untuk UI Hari 4."""

from fastapi import APIRouter, HTTPException

from app.db.koneksi import dapatkan_database
from app.schemas.dashboard import ResponsDashboard
from app.services.dashboard import ambil_ringkasan_dashboard

router = APIRouter(tags=["dashboard"])


@router.get("/api/dashboard", response_model=ResponsDashboard)
async def dashboard_ringkasan() -> ResponsDashboard:
    """Stok kritis, hutang, dan transaksi hari ini dari Atlas."""
    try:
        db = await dapatkan_database()
        return await ambil_ringkasan_dashboard(db)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Gagal memuat dashboard dari Atlas: {e}",
        ) from e
