"""Entry point FastAPI Wargio."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat, health
from app.config import ambil_pengaturan
from app.db.koneksi import tutup_koneksi


@asynccontextmanager
async def siklus_hidup(aplikasi: FastAPI) -> AsyncIterator[None]:
    """Buka/tutup resource saat startup-shutdown."""
    if ambil_pengaturan().mcp_live_enabled:
        from app.services.mcp_klien import mulai_pool_mcp, tutup_pool_mcp

        await mulai_pool_mcp()
    yield
    if ambil_pengaturan().mcp_live_enabled:
        from app.services.mcp_klien import tutup_pool_mcp

        await tutup_pool_mcp()
    await tutup_koneksi()


aplikasi = FastAPI(
    title="Wargio API",
    description="AI agent API for Indonesian micro-retailers",
    version="0.1.0",
    lifespan=siklus_hidup,
)

aplikasi.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

aplikasi.include_router(health.router)
aplikasi.include_router(chat.router)
