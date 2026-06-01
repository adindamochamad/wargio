"""Skema endpoint chat."""

from typing import Optional

from pydantic import BaseModel, Field


class PermintaanChat(BaseModel):
    """Body POST /api/chat."""

    pesan: str = Field(..., min_length=1, max_length=2000, description="Pesan user")


class ResponsChat(BaseModel):
    """Respons sementara Hari 1 — agent penuh di Hari 2."""

    balasan: str
    session_id: Optional[str] = None
    intent: Optional[str] = None
