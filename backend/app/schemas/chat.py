"""Skema endpoint chat."""

from typing import Optional

from pydantic import AliasChoices, BaseModel, Field, model_validator


class PermintaanChat(BaseModel):
    """Body POST /api/chat — terima `pesan` atau `message`."""

    pesan: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Pesan user",
        validation_alias=AliasChoices("pesan", "message"),
    )


class ResponsChat(BaseModel):
    """Respons chat agent Hari 2."""

    balasan: str
    session_id: Optional[str] = None
    intent: Optional[str] = None
    classification_mode: Optional[str] = Field(
        default=None,
        description="gemini atau regex",
    )
