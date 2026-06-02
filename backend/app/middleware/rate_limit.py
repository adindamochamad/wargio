"""Rate limit per sesi atau IP — Hari 5 production."""

from __future__ import annotations

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import ambil_pengaturan

# (kunci, daftar timestamp dalam menit berjalan)
_catatan_permintaan: dict[str, list[float]] = defaultdict(list)


def _ambil_kunci(request: Request) -> str:
    sesi = request.headers.get("X-Session-Id", "").strip()
    if sesi:
        return f"sesi:{sesi}"
    if request.client:
        return f"ip:{request.client.host}"
    return "anonim"


def _bersihkan_dan_hitung(kunci: str, batas: int, sekarang: float) -> bool:
    """True jika masih boleh lanjut, False jika melebihi batas."""
    ambang = sekarang - 60.0
    daftar = _catatan_permintaan[kunci]
    _catatan_permintaan[kunci] = [t for t in daftar if t > ambang]
    if len(_catatan_permintaan[kunci]) >= batas:
        return False
    _catatan_permintaan[kunci].append(sekarang)
    return True


class MiddlewareRateLimit(BaseHTTPMiddleware):
    """Batasi POST /api/chat per menit."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method != "POST" or not request.url.path.startswith("/api/chat"):
            return await call_next(request)

        batas = ambil_pengaturan().rate_limit_per_minute
        if batas <= 0:
            return await call_next(request)

        kunci = _ambil_kunci(request)
        sekarang = time.monotonic()
        if not _bersihkan_dan_hitung(kunci, batas, sekarang):
            return JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        "Terlalu banyak permintaan. Tunggu sebentar lalu coba lagi ya."
                    )
                },
            )

        return await call_next(request)
