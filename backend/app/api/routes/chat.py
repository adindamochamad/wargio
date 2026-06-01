"""Endpoint chat — stub Hari 1, agent penuh Hari 2."""

import uuid

from fastapi import APIRouter, Header

from app.schemas.chat import PermintaanChat, ResponsChat

router = APIRouter(tags=["chat"])


@router.post("/api/chat", response_model=ResponsChat)
async def chat(
    body: PermintaanChat,
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
) -> ResponsChat:
    """
    Menerima pesan user. Hari 1: echo + session id.
    Hari 2+: routing ke Agent Builder + MCP.
    """
    session_id = x_session_id or str(uuid.uuid4())
    return ResponsChat(
        balasan=(
            "Wargio siap. Koneksi agent dan intent engine aktif di Hari 2. "
            f"Pesan Anda diterima ({len(body.pesan)} karakter)."
        ),
        session_id=session_id,
        intent=None,
    )
