"""Endpoint chat — intent engine Hari 2."""

import uuid

from fastapi import APIRouter, Header, HTTPException

from app.db.koneksi import dapatkan_database
from app.schemas.chat import PermintaanChat, ResponsChat
from app.services.executor import proses_pesan
from app.services.sesi import muat_atau_buat_sesi, simpan_pesan
from app.util.lokalisasi import normalisasi_kode_bahasa

router = APIRouter(tags=["chat"])


@router.post("/api/chat", response_model=ResponsChat)
async def chat(
    body: PermintaanChat,
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
    x_wargio_language: str | None = Header(default=None, alias="X-Wargio-Language"),
) -> ResponsChat:
    """Terima pesan, klasifikasi intent, query Atlas, simpan sesi."""
    session_id = x_session_id or str(uuid.uuid4())
    kode_bahasa = normalisasi_kode_bahasa(x_wargio_language)

    try:
        db = await dapatkan_database()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    await muat_atau_buat_sesi(db, session_id)
    await simpan_pesan(db, session_id, "user", body.pesan)

    hasil = await proses_pesan(db, body.pesan, session_id, kode_bahasa=kode_bahasa)

    await simpan_pesan(
        db,
        session_id,
        "assistant",
        hasil["balasan"],
        intent=hasil.get("intent"),
        aksi=hasil.get("actions_taken"),
    )

    return ResponsChat(
        balasan=hasil["balasan"],
        session_id=session_id,
        intent=hasil.get("intent"),
        classification_mode=hasil.get("classification_mode"),
    )
